# Dua Slide Generator

Upload a plain-text duas file → download a ready-to-present `.pptx` using the duas.org template.

## Files

```
app.py            # Streamlit UI
dua_core.py       # Processing logic (no dependencies)
template.pptx     # duas.org branded slide template
requirements.txt  # streamlit only
```

## Text file format

Each dua is 4 lines followed by a blank line:

```
Arabic text
Transliteration
English translation
Urdu translation

Arabic text
...
```

## Deploy to Streamlit Cloud (free)

1. Push this folder to a GitHub repo
2. Go to https://streamlit.io/cloud → New app
3. Point it at your repo, set **Main file** to `app.py`
4. Click Deploy — done, you'll get a public URL

## Run locally

```bash
pip install streamlit
streamlit run app.py
```
