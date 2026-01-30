---

## Installation & Usage

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Set Up Environment

Create a `.env` file with your Google API key:

```env
GOOGLE_API_KEY=your_api_key_here  # right i have my own paid tier api key set up in .env file
```

### Prepare Codebase

1. Create a `codebase/` folder.
2. Add your buggy code (e.g., `app.py`).
3. Add the error trace as `trace.json`.

### Run the System

```bash
python main.py
```

The system will automatically:

1. Find and analyze the `trace.json`.
2. Locate the error source file.
3. Apply a fix.
4. Validate the fix.
5. Report results.

---