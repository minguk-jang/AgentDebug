"""Exploration tools for analyzing web pages."""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime


def analyze_page_structure(driver) -> Dict[str, Any]:
    """
    Analyze the structure of the current web page.

    Args:
        driver: Selenium WebDriver instance

    Returns:
        Dictionary containing page structure analysis
    """
    try:
        from selenium.webdriver.common.by import By

        # Find clickable elements
        clickable_elements = []
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, "button, a, [onclick]")
            for elem in elements[:20]:  # Limit to first 20
                try:
                    text = elem.text.strip()[:50]  # Limit text length
                    tag = elem.tag_name
                    elem_id = elem.get_attribute('id')
                    elem_class = elem.get_attribute('class')

                    selector = f"#{elem_id}" if elem_id else f".{elem_class.split()[0]}" if elem_class else tag

                    clickable_elements.append({
                        "text": text,
                        "tag": tag,
                        "selector": selector,
                        "id": elem_id,
                        "class": elem_class
                    })
                except:
                    continue
        except Exception as e:
            clickable_elements = [{"error": str(e)}]

        # Find input fields
        input_fields = []
        try:
            inputs = driver.find_elements(By.CSS_SELECTOR, "input, textarea, select")
            for inp in inputs[:20]:  # Limit to first 20
                try:
                    inp_type = inp.get_attribute('type') or 'text'
                    inp_id = inp.get_attribute('id')
                    inp_name = inp.get_attribute('name')
                    inp_placeholder = inp.get_attribute('placeholder')

                    selector = f"#{inp_id}" if inp_id else f"[name='{inp_name}']" if inp_name else f"input[type='{inp_type}']"

                    input_fields.append({
                        "type": inp_type,
                        "id": inp_id,
                        "name": inp_name,
                        "placeholder": inp_placeholder,
                        "selector": selector
                    })
                except:
                    continue
        except Exception as e:
            input_fields = [{"error": str(e)}]

        # Find navigation elements
        navigation = []
        try:
            nav_elements = driver.find_elements(By.CSS_SELECTOR, "nav a, .menu a, header a")
            for nav in nav_elements[:15]:  # Limit to first 15
                try:
                    text = nav.text.strip()[:30]
                    href = nav.get_attribute('href')
                    if text or href:
                        navigation.append({
                            "text": text,
                            "href": href
                        })
                except:
                    continue
        except Exception as e:
            navigation = [{"error": str(e)}]

        return {
            "clickable_elements": clickable_elements,
            "input_fields": input_fields,
            "navigation": navigation,
            "page_title": driver.title,
            "current_url": driver.current_url
        }

    except Exception as e:
        return {
            "error": str(e),
            "clickable_elements": [],
            "input_fields": [],
            "navigation": []
        }


def test_action_dry_run(
    driver,
    action_type: str,
    selector: str,
    value: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Test if an action can be performed without actually executing it.

    Args:
        driver: Selenium WebDriver instance
        action_type: Type of action (click, input, navigate)
        selector: Element selector
        value: Value for input actions

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        # Try to locate element
        element = None
        strategies = [
            (By.CSS_SELECTOR, selector),
            (By.XPATH, selector),
            (By.ID, selector.replace('#', '').replace('[id=', '').replace(']', ''))
        ]

        for by_type, sel in strategies:
            try:
                element = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((by_type, sel))
                )
                break
            except:
                continue

        if not element:
            return False, f"Element not found with selector: {selector}"

        # Check action-specific conditions
        if action_type == "click":
            if not element.is_displayed():
                return False, "Element is not visible"
            if not element.is_enabled():
                return False, "Element is not enabled"
            try:
                WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                return True, "Element is clickable"
            except:
                return True, "Element exists but may not be immediately clickable"

        elif action_type == "input":
            tag = element.tag_name.lower()
            if tag not in ['input', 'textarea', 'select']:
                return False, f"Element is not an input field (tag: {tag})"
            if not element.is_enabled():
                return False, "Input field is disabled"
            if value is None:
                return True, "Input field is available (no value to test)"
            return True, f"Input field is ready to receive value: {value[:20]}..."

        elif action_type == "navigate":
            return True, "Navigation action does not require element validation"

        else:
            return False, f"Unknown action type: {action_type}"

    except Exception as e:
        return False, f"Dry run error: {str(e)}"


def capture_interaction_result(
    driver,
    action_type: str,
    before_url: str
) -> Dict[str, Any]:
    """
    Capture the results of an interaction for analysis.

    Args:
        driver: Selenium WebDriver instance
        action_type: Type of action that was performed
        before_url: URL before the action

    Returns:
        Dictionary containing interaction results
    """
    try:
        from selenium.webdriver.common.by import By

        after_url = driver.current_url
        page_changed = before_url != after_url

        # Count new elements (approximate)
        try:
            all_elements = driver.find_elements(By.CSS_SELECTOR, "*")
            new_elements_count = len(all_elements)
        except:
            new_elements_count = 0

        return {
            "action_type": action_type,
            "before_url": before_url,
            "after_url": after_url,
            "page_changed": page_changed,
            "new_elements_count": new_elements_count,
            "timestamp": datetime.now().isoformat(),
            "page_title": driver.title
        }

    except Exception as e:
        return {
            "error": str(e),
            "action_type": action_type,
            "before_url": before_url,
            "timestamp": datetime.now().isoformat()
        }
