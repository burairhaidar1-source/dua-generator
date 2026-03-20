"""
dua_core.py — pure processing logic, no file paths, no UI.
Accepts bytes in, returns bytes out so it works anywhere.
"""

import io, zipfile, re
from xml.dom import minidom

NS_P = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"

ID_ARABIC          = "106"
ID_ENGLISH         = "107"
ID_TRANSLITERATION = "108"
ID_URDU            = "109"


# ── parser ────────────────────────────────────────────────────────────────────

def parse_duas(text: str) -> list[dict]:
    """
    Parse plain text into a list of dua dicts.
    Each set is 4 non-blank lines (Arabic / Transliteration / English / Urdu)
    separated by a blank line.
    """
    sets, buf = [], []
    for raw in text.splitlines():
        s = raw.strip()
        if s:
            buf.append(s)
        else:
            if len(buf) >= 4:
                sets.append({"arabic": buf[0], "transliteration": buf[1],
                              "english": buf[2], "urdu": buf[3]})
            buf = []
    if len(buf) >= 4:
        sets.append({"arabic": buf[0], "transliteration": buf[1],
                     "english": buf[2], "urdu": buf[3]})
    return sets


# ── XML helpers ───────────────────────────────────────────────────────────────

def _first_para(txBody):
    return txBody.getElementsByTagNameNS(NS_A, "p")[0]

def _first_run(para):
    runs = para.getElementsByTagNameNS(NS_A, "r")
    return runs[0] if runs else None

def _set_run_text(run, text):
    for t in run.getElementsByTagNameNS(NS_A, "t"):
        for ch in list(t.childNodes):
            t.removeChild(ch)
        t.appendChild(t.ownerDocument.createTextNode(text))
        break

def _collapse_runs(para, text):
    runs = list(para.getElementsByTagNameNS(NS_A, "r"))
    if not runs:
        return
    _set_run_text(runs[0], text)
    for r in runs[1:]:
        r.parentNode.removeChild(r)

def _remove_placeholder(sp):
    for ph in list(sp.getElementsByTagNameNS(NS_P, "ph")):
        ph.parentNode.removeChild(ph)
    for cNvSpPr in sp.getElementsByTagNameNS(NS_P, "cNvSpPr"):
        cNvSpPr.setAttribute("txBox", "1")
        for lock in list(cNvSpPr.getElementsByTagNameNS(NS_A, "spLocks")):
            cNvSpPr.removeChild(lock)

def _fix_english_style(sp):
    for txBody in sp.getElementsByTagNameNS(NS_P, "txBody"):
        paras = txBody.getElementsByTagNameNS(NS_A, "p")
        if not paras:
            continue
        para = paras[0]
        doc  = para.ownerDocument

        pPr_list = para.getElementsByTagNameNS(NS_A, "pPr")
        pPr = pPr_list[0] if pPr_list else doc.createElementNS(NS_A, "a:pPr")
        if not pPr_list:
            para.insertBefore(pPr, para.firstChild)
        pPr.setAttribute("algn", "ctr")
        pPr.removeAttribute("marL")
        pPr.removeAttribute("indent")

        run = _first_run(para)
        if not run:
            continue
        rPr_list = run.getElementsByTagNameNS(NS_A, "rPr")
        rPr = rPr_list[0] if rPr_list else doc.createElementNS(NS_A, "a:rPr")
        if not rPr_list:
            run.insertBefore(rPr, run.firstChild)
        rPr.setAttribute("sz", "3200")
        rPr.setAttribute("lang", "en-US")

        for sf in list(rPr.getElementsByTagNameNS(NS_A, "solidFill")):
            rPr.removeChild(sf)
        sf  = doc.createElementNS(NS_A, "a:solidFill")
        clr = doc.createElementNS(NS_A, "a:srgbClr")
        clr.setAttribute("val", "0066CC")
        sf.appendChild(clr)
        rPr.appendChild(sf)

def _fix_arabic_align(sp):
    for txBody in sp.getElementsByTagNameNS(NS_P, "txBody"):
        paras = txBody.getElementsByTagNameNS(NS_A, "p")
        if not paras:
            continue
        para = paras[0]
        doc  = para.ownerDocument
        pPr_list = para.getElementsByTagNameNS(NS_A, "pPr")
        pPr = pPr_list[0] if pPr_list else doc.createElementNS(NS_A, "a:pPr")
        if not pPr_list:
            para.insertBefore(pPr, para.firstChild)
        pPr.setAttribute("algn", "ctr")


def _fill_slide_xml(xml_bytes: bytes, dua: dict) -> bytes:
    dom = minidom.parseString(xml_bytes)
    for sp in dom.getElementsByTagNameNS(NS_P, "sp"):
        cNvPr = sp.getElementsByTagNameNS(NS_P, "cNvPr")
        if not cNvPr:
            continue
        sid = cNvPr[0].getAttribute("id")
        txBodies = sp.getElementsByTagNameNS(NS_P, "txBody")
        if not txBodies:
            continue
        txBody = txBodies[0]

        if sid == ID_ARABIC:
            _remove_placeholder(sp)
            _fix_arabic_align(sp)
            run = _first_run(_first_para(txBody))
            if run:
                _set_run_text(run, dua["arabic"])

        elif sid == ID_ENGLISH:
            _remove_placeholder(sp)
            _fix_english_style(sp)
            paras = txBody.getElementsByTagNameNS(NS_A, "p")
            if paras:
                run = _first_run(paras[0])
                if run:
                    _set_run_text(run, dua["english"])

        elif sid == ID_URDU:
            run = _first_run(_first_para(txBody))
            if run:
                _set_run_text(run, dua["urdu"])

        elif sid == ID_TRANSLITERATION:
            paras = txBody.getElementsByTagNameNS(NS_A, "p")
            if paras:
                _collapse_runs(paras[0], dua["transliteration"])

    return dom.toxml(encoding="utf-8")


# ── main public function ──────────────────────────────────────────────────────

def build_pptx_bytes(template_bytes: bytes, duas: list[dict]) -> bytes:
    """
    Given template PPTX as bytes and a list of dua dicts,
    return the generated PPTX as bytes.
    """
    with zipfile.ZipFile(io.BytesIO(template_bytes), "r") as zin:
        names     = zin.namelist()
        file_data = {n: zin.read(n) for n in names}

    prs_dom   = minidom.parseString(file_data["ppt/presentation.xml"])
    slide1_xml  = file_data["ppt/slides/slide1.xml"]
    slide1_rels = file_data.get("ppt/slides/_rels/slide1.xml.rels", b"")

    sld_id_lst   = prs_dom.getElementsByTagNameNS(NS_P, "sldIdLst")[0]
    existing_ids = [int(n.getAttribute("id"))
                    for n in sld_id_lst.getElementsByTagNameNS(NS_P, "sldId")]
    next_slide_id = max(existing_ids) + 1 if existing_ids else 256

    prs_rels_xml  = file_data["ppt/_rels/presentation.xml.rels"].decode("utf-8")
    existing_rids = [int(m) for m in re.findall(r'Id="rId(\d+)"', prs_rels_xml)]
    next_rid_num  = max(existing_rids) + 1 if existing_rids else 1

    content_types_xml = file_data["[Content_Types].xml"].decode("utf-8")
    new_files = {}

    existing_nums = [int(m.group(1)) for n in names
                     if (m := re.match(r"ppt/slides/slide(\d+)\.xml", n))]
    next_slide_num = max(existing_nums) + 1 if existing_nums else 2

    for i, dua in enumerate(duas):
        if i == 0:
            new_files["ppt/slides/slide1.xml"] = _fill_slide_xml(slide1_xml, dua)
        else:
            new_num   = next_slide_num + (i - 1)
            slide_key = f"ppt/slides/slide{new_num}.xml"
            rels_key  = f"ppt/slides/_rels/slide{new_num}.xml.rels"

            new_files[slide_key] = _fill_slide_xml(slide1_xml, dua)

            if slide1_rels:
                rels_str = re.sub(r'\s*<Relationship[^>]*notesSlide[^>]*/>\s*',
                                  "\n", slide1_rels.decode("utf-8"))
                new_files[rels_key] = rels_str.encode("utf-8")

            ct_entry = (f'<Override PartName="/ppt/slides/slide{new_num}.xml" '
                        f'ContentType="application/vnd.openxmlformats-officedocument'
                        f'.presentationml.slide+xml"/>')
            if f"/ppt/slides/slide{new_num}.xml" not in content_types_xml:
                content_types_xml = content_types_xml.replace(
                    "</Types>", f"  {ct_entry}\n</Types>")

            rid = f"rId{next_rid_num + (i - 1)}"
            new_rel = (f'<Relationship Id="{rid}" '
                       f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" '
                       f'Target="slides/slide{new_num}.xml"/>')
            prs_rels_xml = prs_rels_xml.replace(
                "</Relationships>", f"  {new_rel}\n</Relationships>")

            sld_id_elem = prs_dom.createElementNS(NS_P, "p:sldId")
            sld_id_elem.setAttribute("id", str(next_slide_id + (i - 1)))
            sld_id_elem.setAttribute("r:id", rid)
            sld_id_lst.appendChild(sld_id_elem)

    new_files["ppt/presentation.xml"]            = prs_dom.toxml(encoding="utf-8")
    new_files["ppt/_rels/presentation.xml.rels"] = prs_rels_xml.encode("utf-8")
    new_files["[Content_Types].xml"]             = content_types_xml.encode("utf-8")

    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for name in names:
            zout.writestr(name, new_files.get(name, file_data[name]))
        for name, data in new_files.items():
            if name not in names:
                zout.writestr(name, data)

    return out.getvalue()
