"""Web driver utility functions for Selenium automation."""

import re
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def get_driver() -> webdriver.Chrome:
    """
    Initialize and return a Chrome WebDriver with optimal settings.

    Returns:
        Configured Chrome WebDriver instance
    """
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)

        return driver

    except Exception as e:
        raise RuntimeError(f"Failed to initialize WebDriver: {str(e)}")


def safe_find_element(driver, selector: str, timeout: int = 10):
    """
    Safely find an element using multiple selector strategies.

    Args:
        driver: Selenium WebDriver instance
        selector: Element selector (CSS, XPath, or ID)
        timeout: Maximum wait time in seconds

    Returns:
        WebElement if found, None otherwise
    """
    try:
        # Strategy 1: Try CSS selector
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return element
        except:
            pass

        # Strategy 2: Try XPath
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, selector))
            )
            return element
        except:
            pass

        # Strategy 3: Try ID (remove # prefix if present)
        try:
            id_value = selector.replace('#', '').replace('[id=', '').replace(']', '').replace("'", "").replace('"', '')
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.ID, id_value))
            )
            return element
        except:
            pass

        # Strategy 4: Try name attribute
        try:
            # Extract name from selector like [name='value']
            name_match = re.search(r"name=['\"]?([^'\"\\]]+)", selector)
            if name_match:
                name_value = name_match.group(1)
                element = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.NAME, name_value))
                )
                return element
        except:
            pass

        return None

    except Exception as e:
        return None


def safe_click(driver, selector: str) -> bool:
    """
    Safely click an element with multiple fallback strategies.

    Args:
        driver: Selenium WebDriver instance
        selector: Element selector

    Returns:
        True if click succeeded, False otherwise
    """
    try:
        element = safe_find_element(driver, selector)
        if not element:
            return False

        # Scroll element into view
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)

        # Wait a moment for scroll
        import time
        time.sleep(0.5)

        # Try normal click
        try:
            element.click()
            return True
        except:
            pass

        # Try JavaScript click as fallback
        try:
            driver.execute_script("arguments[0].click();", element)
            return True
        except:
            pass

        # Try Actions click as last resort
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(driver)
            actions.move_to_element(element).click().perform()
            return True
        except:
            pass

        return False

    except Exception as e:
        return False


def safe_input(driver, selector: str, value: str) -> bool:
    """
    Safely input text into an element.

    Args:
        driver: Selenium WebDriver instance
        selector: Element selector
        value: Text to input

    Returns:
        True if input succeeded, False otherwise
    """
    try:
        element = safe_find_element(driver, selector)
        if not element:
            return False

        # Scroll element into view
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)

        # Wait a moment for scroll
        import time
        time.sleep(0.5)

        # Clear existing content
        try:
            element.clear()
        except:
            # Try JavaScript clear if normal clear fails
            driver.execute_script("arguments[0].value = '';", element)

        # Input new value
        try:
            element.send_keys(value)
            return True
        except:
            # Try JavaScript input as fallback
            try:
                driver.execute_script(f"arguments[0].value = '{value}';", element)
                # Trigger input event
                driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", element)
                return True
            except:
                return False

    except Exception as e:
        return False


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a string to be used as a filename.

    Args:
        filename: Original filename string

    Returns:
        Sanitized filename string
    """
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)

    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')

    # Remove multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)

    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')

    # Limit length to 50 characters
    sanitized = sanitized[:50]

    # Ensure it's not empty
    if not sanitized:
        sanitized = "output"

    return sanitized
