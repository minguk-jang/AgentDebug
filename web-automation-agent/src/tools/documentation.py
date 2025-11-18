"""Documentation tools for generating Markdown guides."""

from datetime import datetime
from ..agent.state import PlanStep, GuideItem


def init_md_document(url: str, query: str) -> str:
    """
    Initialize a Markdown document with header information.

    Args:
        url: Target URL
        query: User query

    Returns:
        Markdown string with initialized template
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""# Web Automation Guide

**Target URL**: {url}
**Query**: {query}
**Generated**: {timestamp}

---

## Plan

## Guide

"""


def append_plan_step(md_content: str, step: PlanStep) -> str:
    """
    Append a plan step to the Markdown document.

    Args:
        md_content: Current Markdown content
        step: PlanStep to append

    Returns:
        Updated Markdown content
    """
    step_section = f"""### Step {step.step_id}: {step.description}
- **Action**: {step.action_type}
- **Selector**: `{step.selector if step.selector else 'N/A'}`
- **Value**: `{step.value if step.value else 'N/A'}`
- **Status**: {step.status}

"""

    # Insert after "## Plan" section
    plan_marker = "## Plan"
    if plan_marker in md_content:
        parts = md_content.split(plan_marker, 1)
        # Find where the next ## section starts
        after_plan = parts[1]
        next_section_idx = after_plan.find("\n## ")
        if next_section_idx != -1:
            # Insert before next section
            before_next = after_plan[:next_section_idx]
            after_next = after_plan[next_section_idx:]
            md_content = parts[0] + plan_marker + before_next + step_section + after_next
        else:
            # Append to end of Plan section
            md_content = parts[0] + plan_marker + after_plan + step_section
    else:
        # Fallback: append to end
        md_content += step_section

    return md_content


def append_guide_section(md_content: str, guide_item: GuideItem) -> str:
    """
    Append a guide item to the Markdown document.

    Args:
        md_content: Current Markdown content
        guide_item: GuideItem to append

    Returns:
        Updated Markdown content
    """
    # Format category as title
    category_title = guide_item.category.replace('_', ' ').title()

    guide_section = f"""### {category_title} (Step {guide_item.step_id})
{guide_item.content}

"""

    # Insert after "## Guide" section
    guide_marker = "## Guide"
    if guide_marker in md_content:
        parts = md_content.split(guide_marker, 1)
        md_content = parts[0] + guide_marker + parts[1] + guide_section
    else:
        # Fallback: append to end
        md_content += "\n## Guide\n" + guide_section

    return md_content


def finalize_md(md_content: str, output_path: str) -> str:
    """
    Finalize and save the Markdown document to a file.

    Args:
        md_content: Complete Markdown content
        output_path: Path to save the file

    Returns:
        Success message with file path
    """
    try:
        import os

        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        return f"Documentation saved successfully to: {output_path}"

    except Exception as e:
        return f"Error saving documentation: {str(e)}"
