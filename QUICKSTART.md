# CVForge Quick Start Guide

Get started with CVForge in 5 minutes!

## Prerequisites

- Python 3.9 or higher
- Git
- **For PDF generation**: System libraries (see below)

## Important: PDF Generation Setup

WeasyPrint (used for PDF generation) requires system libraries. You have two options:

### Option A: Install System Libraries (Recommended)

**On macOS:**
```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required libraries
brew install pango gdk-pixbuf libffi
```

**On Ubuntu/Debian:**
```bash
sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf2.0-0 libffi-dev
```

### Option B: Skip PDF Generation (Try Other Features First)

You can use all other features without PDF generation:
- CV validation
- Achievement helper
- CV improvement suggestions
- Web UI (view only, no PDF download)

## Setup

### 1. Install Dependencies

```bash
# Make sure you're in the cvmaker directory
cd /Users/cece/cvmaker

# Activate virtual environment (if not already active)
source venv/bin/activate

# Install dependencies (should already be done)
pip install -r requirements.txt
```

### 2. Create Your CV Data

```bash
# Copy the example CV data
cp config/cv_data.example.yaml config/cv_data.yaml

# Edit with your information
nano config/cv_data.yaml
# or use your preferred editor
```

### 3. Configure LLM (Optional)

```bash
# Copy example settings
cp config/settings.example.yaml config/settings.yaml

# Copy environment file
cp .env.example .env

# Add your API key to .env
echo "ANTHROPIC_API_KEY=your_key_here" >> .env
```

## Try It Out!

### Option 1: Achievement Helper Demo (No Setup Required!)

**This works immediately without any configuration:**

```bash
python examples/achievement_helper_example.py
```

Choose **option 3** for a quick demonstration, or **option 2** for a programmatic example.

### Option 2: Validate Your CV Data

```bash
# First, create your CV data file
cp config/cv_data.example.yaml config/cv_data.yaml

# Then validate it
python examples/validate_cv_example.py
```

### Option 3: Simple PDF Generation (Requires System Libraries)

**Only works if you've installed the system libraries above!**

```bash
python examples/simple_pdf_example.py
```

This will generate a PDF from your CV data in the `output/` directory.

### Option 4: CV Improvement Suggestions (Requires LLM)

```bash
python examples/improve_cv_example.py
```

Get AI-powered suggestions to enhance your CV content.

### Option 5: Run the Web Application (View Only Without System Libraries)

```bash
python web/app.py
```

Then open your browser to: http://localhost:5000

Note: PDF download won't work without system libraries, but you can view and manage your CV data.

## What to Try First (In Order of Ease)

1. **Easiest - No Setup Required**: Achievement helper demo
   ```bash
   python examples/achievement_helper_example.py
   # Choose option 3 or 2
   ```

2. **Easy - Minimal Setup**: Validate CV data
   ```bash
   cp config/cv_data.example.yaml config/cv_data.yaml
   python examples/validate_cv_example.py
   ```

3. **Requires System Libraries**: Generate PDF
   ```bash
   # After installing pango, gdk-pixbuf, libffi
   python examples/simple_pdf_example.py
   ```

4. **Requires LLM Setup**: Get AI suggestions
   ```bash
   # After configuring .env with API key
   python examples/improve_cv_example.py
   ```

## Example Workflow

Here's a complete workflow to generate a targeted CV:

```bash
# 1. Validate your CV data
python examples/validate_cv_example.py

# 2. Get improvement suggestions (if LLM configured)
python examples/improve_cv_example.py

# 3. Generate a simple PDF
python examples/simple_pdf_example.py

# 4. Check the output
open output/your_name_cv.pdf
```

## Troubleshooting

### "cannot load library 'gobject-2.0-0'" (WeasyPrint Error)

This means you need to install system libraries for PDF generation:

**macOS:**
```bash
# Install Homebrew first if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Then install libraries
brew install pango gdk-pixbuf libffi
```

**Ubuntu/Debian:**
```bash
sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf2.0-0 libffi-dev
```

**Alternative**: Use features that don't require PDF generation (validation, achievement helper, improvement suggestions)

### "No CV data found"
- Make sure you've copied `config/cv_data.example.yaml` to `config/cv_data.yaml`
- Check that the file path is correct

### "Could not initialize LLM"
- LLM features are optional
- Make sure you've set up `config/settings.yaml` and `.env`
- Check that your API key is valid

### "Module not found"
- Make sure you're in the project directory
- Activate the virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

## Next Steps

- Explore the `examples/` directory for more scripts
- Check `docs/yaml_schema.md` for CV data format details
- Read `README.md` for full documentation
- Try the web UI: `python web/app.py`

## Need Help?

- Check the documentation in `docs/`
- Look at example files in `config/` and `examples/`
- Review the code - it's well-commented!

Happy CV building! 🚀