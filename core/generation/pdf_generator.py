"""
PDF Generation Module

Generates professional, ATS-compliant PDF CVs from templates.
Uses WeasyPrint for HTML to PDF conversion with customizable templates.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

from core.models import CVData, Experience, Achievement


def format_date(date_str: str) -> str:
    """
    Convert YYYY-MM format to 'Month YYYY' format.
    
    Args:
        date_str: Date string in YYYY-MM format
        
    Returns:
        Formatted date string like 'January 2024'
    """
    if not date_str or date_str.lower() == 'present':
        return date_str
    
    try:
        # Parse YYYY-MM format
        date_obj = datetime.strptime(date_str, "%Y-%m")
        return date_obj.strftime("%B %Y")
    except ValueError:
        # If parsing fails, return original
        return date_str


def format_phone(phone_str: str) -> str:
    """
    Format phone number with spaces for better readability.
    Assumes format: +COUNTRY PREFIX NUMBERS
    
    Args:
        phone_str: Phone number string
        
    Returns:
        Formatted phone number
    """
    if not phone_str:
        return phone_str
    
    # Remove all spaces and dashes first
    cleaned = phone_str.replace(' ', '').replace('-', '')
    
    # If it starts with +, format as: +CC PREFIX XXX XXXX
    if cleaned.startswith('+'):
        # Extract country code (assume 1-3 digits after +)
        if len(cleaned) > 4:
            # Try to intelligently split: +CC PREFIX XXX XXXX
            country_code = cleaned[1:3] if len(cleaned) > 10 else cleaned[1:2]
            rest = cleaned[len(country_code)+1:]
            
            if len(rest) >= 7:
                # Format last 7+ digits as XXX XXXX
                prefix = rest[:-7]
                last_seven = rest[-7:]
                formatted_last = f"{last_seven[:3]} {last_seven[3:]}"
                return f"+{country_code} {prefix} {formatted_last}".strip()
    
    return phone_str

logger = logging.getLogger(__name__)


class PDFGenerationError(Exception):
    """Raised when PDF generation fails"""
    pass


class TemplateNotFoundError(PDFGenerationError):
    """Raised when template file is not found"""
    pass


class PDFGenerator:
    """
    Generates PDF CVs from HTML templates using WeasyPrint.
    
    Features:
    - Multiple template support
    - ATS-compliant output
    - Custom CSS styling
    - Font configuration
    - Metadata embedding
    """
    
    def __init__(
        self,
        templates_dir: Optional[Path] = None,
        default_template: str = "default"
    ):
        """
        Initialize PDF generator.
        
        Args:
            templates_dir: Directory containing CV templates (default: templates/cv/)
            default_template: Default template name to use
        """
        if templates_dir is None:
            # Default to templates/cv/ relative to project root
            project_root = Path(__file__).parent.parent.parent
            templates_dir = project_root / "templates" / "cv"
        
        self.templates_dir = Path(templates_dir)
        self.default_template = default_template
        
        # Set up Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Register custom filters
        self.jinja_env.filters['format_date'] = format_date
        self.jinja_env.filters['format_phone'] = format_phone
        
        # Configure fonts for WeasyPrint
        self.font_config = FontConfiguration()
        
        logger.info(f"PDFGenerator initialized with templates from {self.templates_dir}")
    
    def generate_pdf(
        self,
        cv_data: CVData,
        output_path: Path,
        template_name: Optional[str] = None,
        custom_css: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Path:
        """
        Generate PDF CV from CV data.
        
        Args:
            cv_data: Complete CV data
            output_path: Path where PDF should be saved
            template_name: Template to use (default: self.default_template)
            custom_css: Additional CSS to apply
            metadata: PDF metadata (title, author, subject, keywords)
        
        Returns:
            Path to generated PDF file
        
        Raises:
            TemplateNotFoundError: If template file doesn't exist
            PDFGenerationError: If PDF generation fails
        """
        template_name = template_name or self.default_template
        
        try:
            # Render HTML from template
            html_content = self._render_template(cv_data, template_name)
            
            # Generate PDF
            self._html_to_pdf(
                html_content,
                output_path,
                custom_css=custom_css,
                metadata=metadata or self._create_default_metadata(cv_data)
            )
            
            logger.info(f"PDF generated successfully: {output_path}")
            return output_path
            
        except TemplateNotFound as e:
            raise TemplateNotFoundError(
                f"Template '{template_name}.html' not found in {self.templates_dir}"
            ) from e
        except Exception as e:
            raise PDFGenerationError(f"Failed to generate PDF: {str(e)}") from e
    
    def generate_pdf_from_selected_content(
        self,
        personal_info: Dict[str, Any],
        summary: Optional[str],
        experiences: List[Experience],
        skills: Optional[Dict[str, Any]],
        education: Optional[List[Dict[str, Any]]],
        certifications: Optional[List[Dict[str, Any]]] = None,
        projects: Optional[List[Dict[str, Any]]] = None,
        volunteer: Optional[List[Dict[str, Any]]] = None,
        publications: Optional[List[Dict[str, Any]]] = None,
        awards: Optional[List[Dict[str, Any]]] = None,
        output_path: Optional[Path] = None,
        template_name: Optional[str] = None,
        custom_css: Optional[str] = None
    ) -> Path:
        """
        Generate PDF from pre-selected and tailored content.
        
        This is the main method used after content selection and tailoring.
        
        Args:
            personal_info: Personal information dict
            summary: Tailored professional summary
            experiences: Selected and tailored experiences
            skills: Skills data
            education: Education entries
            certifications: Certifications list
            projects: Projects list
            volunteer: Volunteer work list
            publications: Publications list
            awards: Awards list
            output_path: Output PDF path
            template_name: Template to use
            custom_css: Additional CSS
        
        Returns:
            Path to generated PDF
        """
        if output_path is None:
            # Generate default filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name_slug = personal_info.get("name", "cv").lower().replace(" ", "_")
            output_path = Path(f"{name_slug}_cv_{timestamp}.pdf")
        
        template_name = template_name or self.default_template
        
        try:
            # Prepare template context
            context = {
                "personal_info": personal_info,
                "summary": summary,
                "experiences": experiences,
                "skills": skills,
                "education": education,
                "certifications": certifications,
                "projects": projects,
                "volunteer": volunteer,
                "publications": publications,
                "awards": awards,
                "generated_date": datetime.now().strftime("%B %d, %Y")
            }
            
            # Render HTML
            html_content = self._render_template_with_context(context, template_name)
            
            # Create metadata
            metadata = {
                "title": f"{personal_info.get('name', 'CV')} - Curriculum Vitae",
                "author": personal_info.get("name", ""),
                "subject": "Curriculum Vitae",
                "keywords": "CV, Resume, Professional Experience"
            }
            
            # Generate PDF
            self._html_to_pdf(
                html_content,
                output_path,
                custom_css=custom_css,
                metadata=metadata
            )
            
            logger.info(f"PDF generated from selected content: {output_path}")
            return output_path
            
        except Exception as e:
            raise PDFGenerationError(f"Failed to generate PDF: {str(e)}") from e
    
    def _render_template(self, cv_data: CVData, template_name: str) -> str:
        """
        Render HTML template with CV data.
        
        Args:
            cv_data: Complete CV data
            template_name: Name of template (without .html extension)
        
        Returns:
            Rendered HTML string
        """
        template = self.jinja_env.get_template(f"{template_name}.html")
        
        # Prepare context from CVData
        context = {
            "personal_info": cv_data.personal.model_dump(),
            "summary": cv_data.summary,
            "experiences": cv_data.experience,
            "skills": cv_data.skills.model_dump() if cv_data.skills else None,
            "education": cv_data.education,
            "certifications": cv_data.certifications,
            "projects": cv_data.projects,
            "volunteer": cv_data.volunteer,
            "publications": cv_data.publications,
            "awards": cv_data.awards,
            "generated_date": datetime.now().strftime("%B %d, %Y")
        }
        
        return template.render(**context)
    
    def _render_template_with_context(
        self,
        context: Dict[str, Any],
        template_name: str
    ) -> str:
        """
        Render HTML template with custom context.
        
        Args:
            context: Template context dictionary
            template_name: Name of template (without .html extension)
        
        Returns:
            Rendered HTML string
        """
        template = self.jinja_env.get_template(f"{template_name}.html")
        return template.render(**context)
    
    def _html_to_pdf(
        self,
        html_content: str,
        output_path: Path,
        custom_css: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Convert HTML to PDF using WeasyPrint.
        
        Args:
            html_content: HTML string to convert
            output_path: Where to save PDF
            custom_css: Additional CSS to apply
            metadata: PDF metadata
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create HTML object
        html = HTML(string=html_content)
        
        # Prepare stylesheets
        stylesheets = []
        if custom_css:
            stylesheets.append(CSS(string=custom_css, font_config=self.font_config))
        
        # Generate PDF (WeasyPrint 57.2 doesn't support metadata in write_pdf)
        html.write_pdf(
            output_path,
            stylesheets=stylesheets,
            font_config=self.font_config
        )
    
    def _prepare_pdf_metadata(
        self,
        metadata: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Prepare PDF metadata for WeasyPrint.
        
        Args:
            metadata: Metadata dictionary
        
        Returns:
            Formatted metadata for WeasyPrint
        """
        if not metadata:
            return {}
        
        # WeasyPrint expects specific metadata format
        pdf_metadata = {}
        
        if "title" in metadata:
            pdf_metadata["title"] = metadata["title"]
        if "author" in metadata:
            pdf_metadata["author"] = metadata["author"]
        if "subject" in metadata:
            pdf_metadata["subject"] = metadata["subject"]
        if "keywords" in metadata:
            pdf_metadata["keywords"] = metadata["keywords"]
        
        return pdf_metadata
    
    def _create_default_metadata(self, cv_data: CVData) -> Dict[str, str]:
        """
        Create default PDF metadata from CV data.
        
        Args:
            cv_data: CV data
        
        Returns:
            Metadata dictionary
        """
        return {
            "title": f"{cv_data.personal.name} - Curriculum Vitae",
            "author": cv_data.personal.name,
            "subject": "Curriculum Vitae",
            "keywords": "CV, Resume, Professional Experience"
        }
    
    def list_available_templates(self) -> List[str]:
        """
        List all available CV templates.
        
        Returns:
            List of template names (without .html extension)
        """
        if not self.templates_dir.exists():
            return []
        
        templates = []
        for file in self.templates_dir.glob("*.html"):
            templates.append(file.stem)
        
        return sorted(templates)
    
    def preview_html(
        self,
        cv_data: CVData,
        template_name: Optional[str] = None,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate HTML preview without creating PDF.
        
        Useful for debugging templates or web preview.
        
        Args:
            cv_data: CV data
            template_name: Template to use
            output_path: Optional path to save HTML file
        
        Returns:
            Rendered HTML string
        """
        template_name = template_name or self.default_template
        html_content = self._render_template(cv_data, template_name)
        
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html_content, encoding="utf-8")
            logger.info(f"HTML preview saved to {output_path}")
        
        return html_content


def generate_cv_pdf(
    cv_data: CVData,
    output_path: Path,
    template_name: str = "default",
    custom_css: Optional[str] = None
) -> Path:
    """
    Convenience function to generate PDF CV.
    
    Args:
        cv_data: Complete CV data
        output_path: Where to save PDF
        template_name: Template to use
        custom_css: Additional CSS
    
    Returns:
        Path to generated PDF
    """
    generator = PDFGenerator()
    return generator.generate_pdf(
        cv_data,
        output_path,
        template_name=template_name,
        custom_css=custom_css
    )

