"""
Simple PDF Generation Example

Demonstrates basic PDF generation from CV data without LLM tailoring.

Usage:
    python examples/simple_pdf_example.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.data_manager import load_cv_data
from core.generation.pdf_generator import PDFGenerator


def main():
    """Generate a simple PDF from CV data."""
    
    print("=" * 60)
    print("Simple PDF Generation Example")
    print("=" * 60)
    
    # Load CV data
    print("\n[1/2] Loading CV data...")
    cv_data_path = project_root / "config" / "cv_data.yaml"
    
    if not cv_data_path.exists():
        print(f"❌ CV data file not found: {cv_data_path}")
        print("\nPlease create your CV data file:")
        print(f"  cp config/cv_data.example.yaml config/cv_data.yaml")
        print(f"  # Edit config/cv_data.yaml with your information")
        return
    
    cv_data = load_cv_data(str(cv_data_path))
    print(f"✓ Loaded CV for {cv_data.personal_info.name}")
    
    # Generate PDF
    print("\n[2/2] Generating PDF...")
    generator = PDFGenerator()
    
    # Create output directory
    output_dir = project_root / "output"
    output_dir.mkdir(exist_ok=True)
    
    # Generate filename
    name_slug = cv_data.personal_info.name.lower().replace(" ", "_")
    output_path = output_dir / f"{name_slug}_cv.pdf"
    
    # Generate PDF
    pdf_path = generator.generate_pdf(
        cv_data=cv_data,
        output_path=output_path,
        template_name="modern"
    )
    
    print(f"✓ PDF generated successfully!")
    print(f"\nOutput: {pdf_path.absolute()}")
    print(f"Template: modern.html")
    
    # Show available templates
    templates = generator.list_available_templates()
    print(f"\nAvailable templates: {', '.join(templates)}")
    
    print("\n" + "=" * 60)
    print("✓ Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()

