import os
import sys
import time
import re
import argparse
import threading
import queue
import json
from colorama import init, Fore, Style
from playwright.sync_api import sync_playwright
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

init(autoreset=True)

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

def ensure_protocol(url):
    if not url:
        return url
    url = url.strip()
    if not url.lower().startswith(('http://', 'https://')):
        return 'https://' + url
    return url


# User data directory for Playwright session persistence
user_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "playwright_user_data")
os.makedirs(user_data_dir, exist_ok=True)

# Global progress tracking variables
current_progress = 0
total_reports = 0

# Global state for server
server_mode = False
event_queue = queue.Queue()
login_event = threading.Event()
stop_requested = threading.Event()
active_context = None
current_prompt = None
automation_thread = None
is_running_flag = False

def push_event(event_type, data):
    event_queue.put({"type": event_type, "data": data})

def draw_progress_bar(current, total):
    global current_progress, total_reports
    current_progress = current
    total_reports = total
    
    if total == 0:
        return
        
    percent = (current / total) * 100
    bar_length = 30
    filled_length = int(round(bar_length * current / float(total)))
    
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    
    bar = GREEN + '█' * filled_length + RESET + CYAN + '-' * (bar_length - filled_length) + RESET
    
    sys.stdout.write(f'\rReporting Progress: |{bar}| {BOLD}{YELLOW}{percent:.1f}%{RESET} ({BOLD}{current}/{total}{RESET} completed)')
    sys.stdout.flush()
    
    if server_mode:
        push_event("progress", {
            "current": current,
            "total": total,
            "percent": percent
        })

def log_message(msg, level="INFO"):
    sys.stdout.write('\r' + ' ' * 100 + '\r')
    sys.stdout.flush()
    
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    
    timestamp = time.strftime('%I:%M:%S %p')
    
    if level == "INFO":
        level_str = f"{BLUE}{BOLD}[INFO]{RESET}"
    elif level == "WARNING":
        level_str = f"{YELLOW}{BOLD}[WARNING]{RESET}"
    elif level == "ERROR":
        level_str = f"{RED}{BOLD}[ERROR]{RESET}"
    else:
        level_str = f"[{level}]"
        
    print(f"[{timestamp}] {level_str} {msg}")
    
    draw_progress_bar(current_progress, total_reports)
    
    if server_mode:
        push_event("log", {
            "message": msg,
            "level": level,
            "timestamp": timestamp
        })

def wait_for_user(prompt_text, auto_confirm_delay=None):
    if auto_confirm_delay is not None:
        time.sleep(1)
        return

    if server_mode:
        
        global current_prompt
        current_prompt = prompt_text
        push_event("prompt", {"text": prompt_text})
        login_event.clear()
        
        while not login_event.is_set():
            if stop_requested.is_set():
                break
            time.sleep(0.5)
            
        current_prompt = None
        push_event("prompt", {"text": None})
    else:
        input(prompt_text)

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def banner():
    print(Fore.CYAN + r"""
 ███████╗███╗   ███╗ █████╗ ██████╗
 ██╔════╝████╗ ████║██╔══██╗██╔══██╗
 ███████╗██╔████╔██║███████║██████╔╝
 ╚════██║██║╚██╔╝██║██╔══██║██╔══██╗
 ███████║██║ ╚═╝ ██║██║  ██║██║  ██║
 ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝
""")
    print(Fore.YELLOW + "Social-Media-Autonomous-Report")
    print(Fore.BLUE + "=" * 50)

# ==========================================
# FACEBOOK AUTOMATION
# ==========================================
def fb_open_facebook(page, url):
    try:
        page.goto(url)
        log_message("Facebook opened successfully.", "INFO")
    except Exception as e:
        log_message(f"Initial navigation interrupted: {e}", "WARNING")

def fb_navigate_to_profile(page, profile_url):
    profile_url = ensure_protocol(profile_url)
    try:
        page.goto(profile_url)
        log_message(f"Navigated to profile: {profile_url}", "INFO")
    except Exception as e:
        log_message(f"Navigation to profile interrupted: {e}", "WARNING")

def fb_report_profile(page):
    try:
        options_selectors = [
            '[aria-label="See options"]',
            '[aria-label="Action options"]',
            '[aria-label="See Options"]',
            '[aria-label="More"]',
            '[aria-label="Profile actions"]',
            '[aria-label="More actions"]',
            '[aria-label="Options"]',
            '[aria-label="Menu"]',
            '[aria-label*="options" i]',
            '[aria-label*="action" i]',
            '[aria-haspopup="menu"]'
        ]
        
        options_clicked = False
        for selector in options_selectors:
            options_button = page.locator(selector)
            if options_button.count() > 0:
                log_message(f"Options button found using selector: {selector}", "INFO")
                options_button.first.click()
                options_clicked = True
                time.sleep(2)
                break
                
        if not options_clicked:
            log_message("Options button not found.", "WARNING")

        report_button = None
        report_texts = [r"Report profile", r"Find support or report", r"^Report$"]
        
        for text_pattern in report_texts:
            btn = page.get_by_text(re.compile(text_pattern, re.IGNORECASE))
            if btn.count() > 0:
                report_button = btn
                break

        if report_button and report_button.count() > 0:
            log_message("Report button found.", "INFO")
            report_button.first.click()
            time.sleep(2)

            report_account_button = page.get_by_text(re.compile(r"Report Account", re.IGNORECASE))
            if report_account_button.count() > 0:
                report_account_button.first.click()
                log_message("Clicked Report Account.", "INFO")
                time.sleep(2)

            something_about_button = page.get_by_text(re.compile(r"Something about this profile", re.IGNORECASE))
            if something_about_button.count() > 0:
                something_about_button.first.click()
                log_message("Clicked Something about this profile.", "INFO")
                time.sleep(2)

            bullying_abuse_button = page.get_by_text(re.compile(r"Bullying, harassment or abuse", re.IGNORECASE))
            if bullying_abuse_button.count() > 0:
                bullying_abuse_button.first.click()
                log_message("Clicked Bullying, harassment or abuse.", "INFO")
                time.sleep(2)

            bullying_button = page.get_by_text(re.compile(r"Bullying or harassment", re.IGNORECASE))
            if bullying_button.count() > 0:
                bullying_button.first.click()
                log_message("Clicked Bullying or harassment.", "INFO")
                time.sleep(2)

            me_button = page.get_by_text(re.compile(r"^Me$", re.IGNORECASE))
            if me_button.count() > 0:
                me_button.first.click()
                log_message("Clicked Me.", "INFO")
                time.sleep(2)

            submit_button = page.get_by_role("button", name=re.compile(r"Submit", re.IGNORECASE))
            if submit_button.count() > 0:
                submit_button.first.click(force=True)
                log_message("Clicked Submit.", "INFO")
                time.sleep(2)

            next_button = page.get_by_role("button", name=re.compile(r"Next", re.IGNORECASE))
            if next_button.count() > 0:
                next_button.first.click(force=True)
                log_message("Clicked Next.", "INFO")
                time.sleep(2)

            done_button = page.get_by_role("button", name=re.compile(r"Done", re.IGNORECASE))
            if done_button.count() > 0:
                done_button.first.click(force=True)
                log_message("Clicked Done.", "INFO")
                time.sleep(2)

            return True
        return False
    except Exception as e:
        log_message(f"Error reporting profile: {e}", "ERROR")
        return False

# ==========================================
# INSTAGRAM AUTOMATION
# ==========================================
def ig_open_instagram(page, url):
    try:
        page.goto(url)
        log_message("Instagram opened successfully.", "INFO")
    except Exception as e:
        log_message(f"Initial navigation interrupted (likely a redirect): {e}", "WARNING")

def ig_navigate_to_profile(page, profile_url):
    profile_url = ensure_protocol(profile_url)
    try:
        page.goto(profile_url)
        log_message(f"Navigated to profile: {profile_url}", "INFO")
    except Exception as e:
        log_message(f"Navigation to profile interrupted (likely by an Instagram security check or redirect): {e}", "WARNING")

def ig_report_profile(page):
    try:
        options_button = page.locator('[aria-label="Options"]')
        if options_button.count() > 0:
            log_message("Options button found.", "INFO")
            options_button.first.click()
            time.sleep(1)
        else:
            log_message("Options button not found. Searching for Report button directly.", "WARNING")

        report_button = page.locator('text=Report')
        if report_button.count() > 0:
            log_message("Report button found.", "INFO")
            report_button.first.click()
            log_message("Report button clicked.", "INFO")
            time.sleep(1)

            report_account_button = page.locator('text=Report Account')
            report_account_button.first.click()
            log_message("Report Account button clicked.", "INFO")
            time.sleep(1)

            content_issue_button = page.locator("text=It's posting content that shouldn't be on Instagram")
            content_issue_button.first.click()
            log_message("It's posting content that shouldn't be on Instagram button clicked.", "INFO")
            time.sleep(1)

            nudity_button_1 = page.locator('text="Nudity or sexual activity"')
            nudity_button_1.first.click()
            log_message("First Nudity or sexual activity button clicked.", "INFO")
            time.sleep(1)

            nudity_button_2 = page.locator('text="Nudity or sexual activity"')
            nudity_button_2.first.click()
            log_message("Second Nudity or sexual activity button clicked.", "INFO")
            time.sleep(1)

            close_button = page.locator('text=Close')
            close_button.first.click()
            log_message("Close button clicked.", "INFO")

            log_message("Waiting 1 seconds to finalize the report.", "INFO")
            time.sleep(1)

            return True
        else:
            log_message("No Report button found on the page.", "WARNING")
            return False
    except Exception as e:
        log_message(f"Error reporting profile: {e}", "ERROR")
        return False

# ==========================================
# THREADS AUTOMATION
# ==========================================
def th_open_threads(page, url):
    try:
        page.goto(url, wait_until="domcontentloaded")
        log_message("Threads opened successfully.", "INFO")
    except Exception as e:
        log_message(f"Initial navigation interrupted: {e}", "WARNING")

def th_navigate_to_profile(page, profile_url):
    profile_url = ensure_protocol(profile_url)
    try:
        page.goto(profile_url, wait_until="domcontentloaded")
        log_message(f"Navigated to profile: {profile_url}", "INFO")
    except Exception as e:
        log_message(f"Navigation to profile interrupted (likely login redirect): {e}", "WARNING")

def th_report_profile(page):
    try:
        time.sleep(5)
        clicked = False
        try:
            page.wait_for_timeout(2000)
            more_selectors = [
                'svg[aria-label="More"]',
                '[aria-label="More"]',
                'svg:has(title:text-is("More"))'
            ]
            
            for selector in more_selectors:
                elements = page.locator(selector)
                visible_elements = []
                for i in range(elements.count()):
                    el = elements.nth(i)
                    if el.is_visible():
                        visible_elements.append(el)
                
                if visible_elements:
                    try:
                        target_el = visible_elements[1] if len(visible_elements) > 1 else visible_elements[0]
                        target_el.click()
                        log_message(f"Clicked visible profile 'More' button using selector: {selector}", "INFO")
                        clicked = True
                        time.sleep(2)
                        break
                    except Exception as e:
                        log_message(f"Selector {selector} click failed: {e}", "INFO")
                        pass
            
            if not clicked:
                log_message("Could not find 'More' button beside the notify button.", "ERROR")
                return False
                
        except Exception as e:
            log_message(f"Failed to click 'More' button: {e}", "ERROR")
            return False

        try:
            report_selectors = [
                'div[role="button"]:has-text("Report")',
                'span:has-text("Report")',
                'div[role="menuitem"]:has-text("Report")',
                'text="Report"'
            ]
            report_clicked = False
            for selector in report_selectors:
                el = page.locator(selector)
                if el.count() > 0:
                    try:
                        el.last.click(force=True)
                        log_message(f"Clicked 'Report' button using selector: {selector}", "INFO")
                        report_clicked = True
                        time.sleep(2)
                        break
                    except:
                        pass
            if not report_clicked:
                log_message("Could not find 'Report' button in the menu.", "ERROR")
                return False
        except Exception as e:
            log_message(f"Failed to click 'Report' button: {e}", "ERROR")
            return False

        try:
            report_acc_selectors = [
                'div[role="button"]:has-text("Report Account")',
                'span:has-text("Report Account")',
                'div:text-is("Report Account")',
                'text="Report Account"'
            ]
            acc_clicked = False
            for selector in report_acc_selectors:
                el = page.locator(selector)
                if el.count() > 0:
                    try:
                        el.first.click(force=True)
                        log_message(f"Clicked 'Report Account' using selector: {selector}", "INFO")
                        acc_clicked = True
                        time.sleep(2)
                        break
                    except:
                        pass
            if not acc_clicked:
                log_message("Could not find 'Report Account' option.", "ERROR")
                return False
        except Exception as e:
            log_message(f"Failed to click 'Report Account': {e}", "ERROR")
            return False

        try:
            content_selectors = [
                'div[role="button"]:has-text("It\'s posting content that shouldn\'t be on Threads.")',
                'div:text-is("It\'s posting content that shouldn\'t be on Threads.")',
                'text="It\'s posting content that shouldn\'t be on Threads."'
            ]
            content_clicked = False
            for selector in content_selectors:
                el = page.locator(selector)
                if el.count() > 0:
                    try:
                        el.first.click(force=True)
                        log_message("Clicked 'It's posting content that shouldn't be on Threads.'", "INFO")
                        content_clicked = True
                        time.sleep(2)
                        break
                    except:
                        pass
            if not content_clicked:
                log_message("Could not find content option.", "ERROR")
                return False
        except Exception as e:
            log_message(f"Failed to click content option: {e}", "ERROR")
            return False

        try:
            bullying_selectors = [
                'div[role="button"]:has-text("Bullying or unwanted contact")',
                'div:text-is("Bullying or unwanted contact")',
                'text="Bullying or unwanted contact"'
            ]
            bullying_clicked = False
            for selector in bullying_selectors:
                el = page.locator(selector)
                if el.count() > 0:
                    try:
                        el.first.click(force=True)
                        log_message("Clicked 'Bullying or unwanted contact'.", "INFO")
                        bullying_clicked = True
                        time.sleep(2)
                        break
                    except:
                        pass
            if not bullying_clicked:
                log_message("Could not find 'Bullying or unwanted contact'.", "ERROR")
                return False
        except Exception as e:
            log_message(f"Failed to click 'Bullying or unwanted contact': {e}", "ERROR")
            return False

        try:
            harass_selectors = [
                 'div[role="button"]:has-text("Bullying or harassment")',
                 'div:text-is("Bullying or harassment")',
                 'text="Bullying or harassment"'
            ]
            harass_clicked = False
            for selector in harass_selectors:
                el = page.locator(selector)
                if el.count() > 0:
                    try:
                        el.first.click(force=True)
                        log_message("Clicked 'Bullying or harassment'.", "INFO")
                        harass_clicked = True
                        time.sleep(2)
                        break
                    except:
                        pass
            if not harass_clicked:
                log_message("Could not find 'Bullying or harassment'.", "ERROR")
                return False
        except Exception as e:
            log_message(f"Failed to click 'Bullying or harassment': {e}", "ERROR")
            return False

        try:
            me_selectors = [
                'div[role="button"]:has-text("Me")',
                'div:text-is("Me")',
                'text="Me"'
            ]
            me_clicked = False
            for selector in me_selectors:
                el = page.locator(selector)
                if el.count() > 0:
                    try:
                        el.first.click(force=True)
                        log_message("Clicked 'Me' button.", "INFO")
                        me_clicked = True
                        time.sleep(2)
                        break
                    except:
                        pass
            if not me_clicked:
                log_message("Could not find 'Me' button.", "ERROR")
                return False
        except Exception as e:
            log_message(f"Failed to click 'Me' button: {e}", "ERROR")
            return False

        try:
            yes_selectors = [
                'div[role="button"]:has-text("Yes")',
                'div:text-is("Yes")',
                'text="Yes"'
            ]
            yes_clicked = False
            for selector in yes_selectors:
                el = page.locator(selector)
                if el.count() > 0:
                    try:
                        el.first.click(force=True)
                        log_message("Clicked 'Yes' button.", "INFO")
                        yes_clicked = True
                        time.sleep(3)
                        break
                    except:
                        pass
            if not yes_clicked:
                log_message("Could not find 'Yes' button.", "ERROR")
                return False
        except Exception as e:
            log_message(f"Failed to click 'Yes' button: {e}", "ERROR")
            return False

        try:
            done_selectors = [
                 'div[role="button"]:has-text("Done")',
                 'button:has-text("Done")',
                 'div:text-is("Done")',
                 'text="Done"'
            ]
            done_clicked = False
            for selector in done_selectors:
                el = page.locator(selector)
                if el.count() > 0:
                    try:
                        el.first.click(force=True)
                        log_message("Clicked 'Done' button.", "INFO")
                        done_clicked = True
                        time.sleep(2)
                        break
                    except:
                        pass
            if not done_clicked:
                log_message("Could not find 'Done' button.", "ERROR")
                return False
        except Exception as e:
            log_message(f"Failed to click 'done' button: {e}", "ERROR")
            return False

        return True
    except Exception as e:
        log_message(f"Error reporting profile: {e}", "ERROR")
        return False

# ==========================================
# TIKTOK AUTOMATION
# ==========================================
def tt_report_profile(page, profile_url):
    profile_url = ensure_protocol(profile_url)
    try:
        page.goto(profile_url)
        time.sleep(5)
        
        actions_selectors = [
            '[data-e2e="user-more"]',
            '[aria-label="Actions"]'
        ]
        
        actions_clicked = False
        for selector in actions_selectors:
            actions_button = page.locator(selector)
            if actions_button.count() > 0:
                actions_button.first.click()
                log_message("Actions menu opened.", "INFO")
                actions_clicked = True
                time.sleep(2)
                break
                
        if not actions_clicked:
            log_message("Could not find the actions menu button.", "WARNING")
            return False
            
        report_button = page.locator('text="Report"')
        if report_button.count() > 0:
            report_button.first.click()
            log_message("Report button clicked.", "INFO")
            time.sleep(2)

            report_account = page.locator('text="Report account"')
            if report_account.count() > 0:
                report_account.first.click()
                log_message("Clicked 'Report account'.", "INFO")
                time.sleep(2)
            else:
                log_message("Could not find 'Report account'.", "WARNING")
                return False

            something_else = page.locator('text="Something else"')
            if something_else.count() > 0:
                something_else.first.click()
                log_message("Clicked 'Something else'.", "INFO")
                time.sleep(2)
            else:
                log_message("Could not find 'Something else'.", "WARNING")
                return False

            hate_harass = page.locator('text="Hate and harassment"')
            if hate_harass.count() > 0:
                hate_harass.first.click()
                log_message("Clicked 'Hate and harassment'.", "INFO")
                time.sleep(2)
            else:
                log_message("Could not find 'Hate and harassment'.", "WARNING")
                return False

            hate_speech = page.locator('text="Hate speech and hateful behaviors"')
            if hate_speech.count() > 0:
                hate_speech.first.click()
                log_message("Clicked 'Hate speech and hateful behaviors'.", "INFO")
                time.sleep(2)
            else:
                log_message("Could not find 'Hate speech and hateful behaviors'.", "WARNING")
                return False

            submit_btn = page.locator('text="Submit"')
            if submit_btn.count() > 0:
                submit_btn.first.click()
                log_message("Clicked 'Submit'.", "INFO")
                time.sleep(3)
            else:
                log_message("Could not find 'Submit' button.", "WARNING")
                return False

            done_btn = page.locator('text="Done"')
            if done_btn.count() > 0:
                done_btn.first.click()
                log_message("Clicked 'Done'. Report submitted successfully.", "INFO")
                time.sleep(2)
                return True
            else:
                log_message("Could not find 'Done' button.", "WARNING")
                return True
        else:
            log_message("Could not find the report button.", "WARNING")
            return False
            
    except Exception as e:
        log_message(f"Error reporting profile: {e}", "ERROR")
        return False

# ==========================================
# TWITTER AUTOMATION
# ==========================================
def tw_report_profile(page, profile_url):
    profile_url = ensure_protocol(profile_url)
    try:
        page.goto(profile_url)
        time.sleep(5)
        
        more_selectors = [
            '[data-testid="userActions"]',
            '[aria-label="More"]'
        ]
        
        menu_clicked = False
        for selector in more_selectors:
            btn = page.locator(selector)
            if btn.count() > 0:
                btn.first.click()
                log_message("Profile options menu opened.", "INFO")
                menu_clicked = True
                time.sleep(2)
                break
                
        if not menu_clicked:
            log_message("Could not find the profile options menu.", "WARNING")
            return False

        report_btn = page.locator('[data-testid="report"]')
        if report_btn.count() == 0:
            report_btn = page.locator('div[role="menuitem"]:has-text("Report")')

        if report_btn.count() > 0:
            report_btn.first.click()
            log_message("Report button clicked.", "INFO")
            time.sleep(2)
            
            hate_btn = page.locator('text="Hate, Abuse, or Harassment"')
            if hate_btn.count() > 0:
                hate_btn.first.click()
                log_message("Selected Hate, Abuse, or Harassment.", "INFO")
                time.sleep(2)
            else:
                log_message("Could not find Hate, Abuse, or Harassment option.", "WARNING")
                return False
                
            next_btn = page.locator('text="Next"')
            if next_btn.count() > 0:
                next_btn.first.click()
                log_message("Next button clicked.", "INFO")
                time.sleep(2)
            else:
                log_message("Could not find Next button.", "WARNING")
                return False
                
            done_btn = page.locator('text="Done"')
            if done_btn.count() > 0:
                done_btn.first.click()
                log_message("Done button clicked.", "INFO")
                time.sleep(2)
                
            return True
        else:
            log_message("Could not find the report button.", "WARNING")
            return False
            
    except Exception as e:
        log_message(f"Error reporting profile: {e}", "ERROR")
        return False

# ==========================================
# LAUNCH RUNNERS
# ==========================================
def run_facebook(profile_url, report_limit):
    global active_context
    with sync_playwright() as p:
        try:
            context = p.chromium.launch_persistent_context(user_data_dir=user_data_dir, channel='chrome', headless=False, args=["--test-type"])
            active_context = context
            page = context.pages[0]
            fb_open_facebook(page, 'https://www.facebook.com/')
            wait_for_user("Please log in to Facebook and press Enter to continue...", None)

            # Verification loop to handle CAPTCHAs, 2FA, and checkpoint screens
            while not stop_requested.is_set():
                current_url = page.url
                
                # Check if still on the login page
                is_on_login_page = (
                    "login" in current_url or 
                    page.locator("button[name='login']").count() > 0 or 
                    page.locator("a[data-testid='open-registration-form-button']").count() > 0
                )
                
                # Check for checkpoints, 2FA, or CAPTCHA indicators
                is_checkpoint = (
                    "checkpoint" in current_url or 
                    "two_step_verification" in current_url or 
                    "captcha" in current_url or 
                    "security" in current_url
                )
                
                has_captcha_element = False
                try:
                    has_captcha_element = (
                        page.locator("iframe[src*='captcha']").count() > 0 or
                        page.locator("iframe[title*='recaptcha']").count() > 0 or
                        page.locator("input[name='approvals_code']").count() > 0 or
                        page.locator("text='Security checkpoint'").count() > 0 or
                        page.locator("text='Enter security code'").count() > 0
                    )
                except Exception:
                    pass
                
                if is_checkpoint or has_captcha_element:
                    log_message("Security checkpoint, 2FA, or CAPTCHA detected. Please complete it in the Chrome browser.", "WARNING")
                    wait_for_user("A security checkpoint or CAPTCHA was detected. Please complete the verification in the browser and then press Enter/Confirm Logged In...", None)
                elif is_on_login_page:
                    log_message("You are not logged in. Please log in to Facebook first.", "WARNING")
                    wait_for_user("Please log in to Facebook first and then press Enter/Confirm Logged In...", None)
                else:
                    log_message("Login successfully verified. Proceeding to target profile...", "INFO")
                    break
            draw_progress_bar(0, report_limit)
            for i in range(report_limit):
                if stop_requested.is_set():
                    break
                fb_navigate_to_profile(page, profile_url)
                if stop_requested.is_set():
                    break
                time.sleep(1)
                fb_report_profile(page)
                if stop_requested.is_set():
                    break
                time.sleep(1)
                draw_progress_bar(i + 1, report_limit)
            print("\nProcess finished.")
            wait_for_user("Press Enter to close the browser...", 5)
        except Exception as e:
            if stop_requested.is_set():
                log_message("Automation stopped by user.", "WARNING")
            else:
                log_message(f"Error in Facebook automation: {e}", "ERROR")
        finally:
            try:
                context.close()
            except:
                pass
            active_context = None

def run_instagram(profile_url, report_limit):
    global active_context
    with sync_playwright() as p:
        try:
            context = p.chromium.launch_persistent_context(user_data_dir=user_data_dir, channel='chrome', headless=False, args=["--test-type"])
            active_context = context
            page = context.pages[0]
            ig_open_instagram(page, 'https://www.instagram.com/')
            wait_for_user("Please log in to Instagram and press Enter to continue...", None)
            time.sleep(1)
            draw_progress_bar(0, report_limit)
            for i in range(report_limit):
                if stop_requested.is_set():
                    break
                ig_navigate_to_profile(page, profile_url)
                if stop_requested.is_set():
                    break
                time.sleep(1)
                ig_report_profile(page)
                if stop_requested.is_set():
                    break
                time.sleep(1)
                draw_progress_bar(i + 1, report_limit)
            print("\nProcess finished.")
            wait_for_user("Press Enter to close the browser...", 5)
        except Exception as e:
            if stop_requested.is_set():
                log_message("Automation stopped by user.", "WARNING")
            else:
                log_message(f"Error in Instagram automation: {e}", "ERROR")
        finally:
            try:
                context.close()
            except:
                pass
            active_context = None

def run_threads(profile_url, report_limit):
    global active_context
    with sync_playwright() as p:
        try:
            context = p.chromium.launch_persistent_context(user_data_dir=user_data_dir, channel='chrome', headless=False, args=["--test-type"])
            active_context = context
            page = context.pages[0]
            th_open_threads(page, 'https://www.threads.com/')
            wait_for_user("Please log in to Threads and press Enter to continue...", None)

            # Verification loop to handle security checks, 2FA, phone verification, and checkpoint screens on Threads/Instagram login
            while not stop_requested.is_set():
                current_url = page.url
                
                # Check if still on the login page
                is_on_login_page = (
                    "login" in current_url or 
                    page.locator("button[type='submit']:has-text('Log in')").count() > 0 or
                    page.locator("text='Log in with Instagram'").count() > 0
                )
                
                # Check for checkpoints, 2FA, phone verification, or security challenges
                is_checkpoint = (
                    "checkpoint" in current_url or 
                    "challenge" in current_url or
                    "two-factor" in current_url or 
                    "security" in current_url or
                    "phone" in current_url
                )
                
                has_verification_element = False
                try:
                    has_verification_element = (
                        page.locator("input[name='security_code']").count() > 0 or
                        page.locator("input[type='tel']").count() > 0 or
                        page.locator("text='Enter your security code'").count() > 0 or
                        page.locator("text='Help us confirm it's you'").count() > 0 or
                        page.locator("text='Verification'").count() > 0 or
                        page.locator("text='Confirm it's You'").count() > 0
                    )
                except Exception:
                    pass
                
                if is_checkpoint or has_verification_element:
                    log_message("Security checkpoint, 2FA, or verification screen detected. Please complete the verification in the Chrome browser.", "WARNING")
                    wait_for_user("A security checkpoint or verification screen was detected. Please complete it in the browser and then press Enter/Confirm Logged In...", None)
                elif is_on_login_page:
                    log_message("You are not logged in. Please log in to Threads/Instagram first.", "WARNING")
                    wait_for_user("Please log in first and then press Enter/Confirm Logged In...", None)
                else:
                    log_message("Login successfully verified. Proceeding to target profile...", "INFO")
                    break
            draw_progress_bar(0, report_limit)
            for i in range(report_limit):
                if stop_requested.is_set():
                    break
                th_navigate_to_profile(page, profile_url)
                if stop_requested.is_set():
                    break
                th_report_profile(page)
                if stop_requested.is_set():
                    break
                time.sleep(5)
                draw_progress_bar(i + 1, report_limit)
            print("\nProcess finished.")
            wait_for_user("Press Enter to close the browser...", 5)
        except Exception as e:
            if stop_requested.is_set():
                log_message("Automation stopped by user.", "WARNING")
            else:
                log_message(f"Error in Threads automation: {e}", "ERROR")
        finally:
            try:
                context.close()
            except:
                pass
            active_context = None

def run_tiktok(profile_url, report_limit):
    global active_context
    with sync_playwright() as p:
        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir, channel='chrome', headless=False,
                ignore_default_args=["--enable-automation"], args=["--disable-blink-features=AutomationControlled", "--test-type"]
            )
            active_context = context
            page = context.pages[0]
            draw_progress_bar(0, report_limit)
            for i in range(report_limit):
                if stop_requested.is_set():
                    break
                tt_report_profile(page, profile_url)
                if stop_requested.is_set():
                    break
                time.sleep(2)
                draw_progress_bar(i + 1, report_limit)
            print("\nProcess finished.")
            wait_for_user("Press Enter to close the browser...", 5)
        except Exception as e:
            if stop_requested.is_set():
                log_message("Automation stopped by user.", "WARNING")
            else:
                log_message(f"Error in TikTok automation: {e}", "ERROR")
        finally:
            try:
                context.close()
            except:
                pass
            active_context = None

def run_twitter(profile_url, report_limit):
    global active_context
    with sync_playwright() as p:
        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir, channel='chrome', headless=False,
                ignore_default_args=["--enable-automation"], args=["--disable-blink-features=AutomationControlled", "--start-maximized", "--disable-infobars", "--test-type"], no_viewport=True
            )
            active_context = context
            page = context.pages[0]
            try:
                page.goto('https://twitter.com/')
                log_message("Twitter opened for login.", "INFO")
            except Exception as e:
                log_message(f"Initial navigation interrupted: {e}", "WARNING")
            wait_for_user("Please log in to Twitter and press Enter to continue...", None)
            draw_progress_bar(0, report_limit)
            for i in range(report_limit):
                if stop_requested.is_set():
                    break
                tw_report_profile(page, profile_url)
                if stop_requested.is_set():
                    break
                time.sleep(2)
                draw_progress_bar(i + 1, report_limit)
            print("\nProcess finished.")
            wait_for_user("Press Enter to close the browser...", 5)
        except Exception as e:
            if stop_requested.is_set():
                log_message("Automation stopped by user.", "WARNING")
            else:
                log_message(f"Error in Twitter automation: {e}", "ERROR")
        finally:
            try:
                context.close()
            except:
                pass
            active_context = None

# ==========================================
# FLASK WEB SERVER
# ==========================================
app = Flask(__name__)
CORS(app)

def run_automation_in_background(platform, url, count):
    global is_running_flag, stop_requested
    is_running_flag = True
    stop_requested.clear()
    login_event.clear()
    
    push_event("status", {"isRunning": True, "status": "running"})
    push_event("progress", {"current": 0, "total": count, "percent": 0.0})
    
    try:
        if platform == 'facebook':
            run_facebook(url, count)
        elif platform == 'instagram':
            run_instagram(url, count)
        elif platform == 'threads':
            run_threads(url, count)
        elif platform == 'tiktok':
            run_tiktok(url, count)
        elif platform == 'twitter':
            run_twitter(url, count)
            
        if stop_requested.is_set():
            push_event("status", {"isRunning": False, "status": "stopped"})
            push_event("log", {"message": "Automation terminated by user.", "level": "WARNING", "timestamp": time.strftime('%I:%M:%S %p')})
        else:
            push_event("status", {"isRunning": False, "status": "completed"})
            push_event("log", {"message": "Automation completed successfully.", "level": "INFO", "timestamp": time.strftime('%I:%M:%S %p')})
    except Exception as e:
        log_message(f"Unhandled thread error: {e}", "ERROR")
        push_event("status", {"isRunning": False, "status": "error"})
    finally:
        is_running_flag = False

@app.route('/api/start', methods=['POST'])
def api_start():
    global automation_thread, is_running_flag
    if is_running_flag:
        return jsonify({"error": "Automation is already running"}), 400
        
    data = request.json
    platform = data.get('platform', '').strip().lower()
    url = data.get('url', '').strip()
    count = data.get('count', 1)
    
    if not platform or not url:
        return jsonify({"error": "Platform and URL are required"}), 400
        
    url = ensure_protocol(url)
    url_lower = url.lower()
    
    # Backend URL verification matching the frontend validation constraints
    is_valid = False
    if platform == 'facebook':
        is_valid = 'facebook.com' in url_lower or 'fb.com' in url_lower
    elif platform == 'instagram':
        is_valid = 'instagram.com' in url_lower
    elif platform == 'threads':
        is_valid = 'threads.net' in url_lower or 'threads.com' in url_lower
    elif platform == 'tiktok':
        is_valid = 'tiktok.com' in url_lower
    elif platform == 'twitter':
        is_valid = 'twitter.com' in url_lower or 'x.com' in url_lower
    else:
        is_valid = True
        
    if not is_valid:
        return jsonify({"error": f"Invalid URL for target platform '{platform}'. Please provide a valid {platform} link."}), 400
        
    automation_thread = threading.Thread(
        target=run_automation_in_background,
        args=(platform, url, count),
        daemon=True
    )
    automation_thread.start()
    return jsonify({"status": "started"})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    global stop_requested
    stop_requested.set()
    login_event.set()
    return jsonify({"status": "stopping"})

@app.route('/api/confirm-login', methods=['POST'])
def api_confirm_login():
    login_event.set()
    return jsonify({"status": "confirmed"})

@app.route('/api/events', methods=['GET'])
def api_events():
    def event_generator():
        while not event_queue.empty():
            try:
                event_queue.get_nowait()
            except queue.Empty:
                break
                
        initial_status = "running" if is_running_flag else "idle"
        yield f"data: {json.dumps({'type': 'status', 'data': {'isRunning': is_running_flag, 'status': initial_status}})}\n\n"
        if current_prompt:
            yield f"data: {json.dumps({'type': 'prompt', 'data': {'text': current_prompt}})}\n\n"
            
        while True:
            try:
                evt = event_queue.get(timeout=15.0)
                yield f"data: {json.dumps(evt)}\n\n"
            except queue.Empty:
                yield ": keepalive\n\n"
            except Exception:
                break
                
    return Response(event_generator(), mimetype='text/event-stream')

def start_server():
    global server_mode
    server_mode = True
    print("Starting SMAR API Server on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

# ==========================================
# MAIN ENTRY
# ==========================================
def interactive_menu():
    while True:
        clear()
        banner()
        print(Fore.GREEN + "\n[1] Facebook")
        print(Fore.MAGENTA + "[2] Instagram")
        print(Fore.CYAN + "[3] Twitter / X")
        print(Fore.RED + "[4] TikTok")
        print(Fore.YELLOW + "[5] Threads")
        print(Fore.BLUE + "[6] Exit")

        choice = input(Fore.LIGHTCYAN_EX + "\n┌─────────────────────────────┐\n│ SMAR > ").strip()

        if choice == "6":
            print(Fore.YELLOW + "\nExiting SMAR. Goodbye!")
            sys.exit(0)
            
        if choice not in ["1", "2", "3", "4", "5"]:
            print(Fore.RED + "\nInvalid option.")
            input(Fore.YELLOW + "Press Enter to continue...")
            continue

        url = input("Enter the profile URL to report: ").strip()
        count_str = input("Enter the number of times to report the account: ").strip()
        
        try:
            count = int(count_str)
        except ValueError:
            print("Invalid number.")
            input(Fore.YELLOW + "Press Enter to continue...")
            continue
            
        if choice == "1":
            run_facebook(url, count)
        elif choice == "2":
            run_instagram(url, count)
        elif choice == "3":
            run_twitter(url, count)
        elif choice == "4":
            run_tiktok(url, count)
        elif choice == "5":
            run_threads(url, count)

def main():
    parser = argparse.ArgumentParser(description="Social-Media-Autonomous-Report (SMAR)")
    parser.add_argument('--platform', choices=['facebook', 'instagram', 'threads', 'tiktok', 'twitter'], help="Target platform")
    parser.add_argument('--url', help="Profile URL to report")
    parser.add_argument('--count', type=int, help="Number of reports to send")
    parser.add_argument('--server', action='store_true', help="Run SMAR as local Flask API server")

    args = parser.parse_args()

    if args.server:
        start_server()
    elif not args.platform or not args.url or not args.count:
        interactive_menu()
    else:
        if args.platform == 'facebook':
            run_facebook(args.url, args.count)
        elif args.platform == 'instagram':
            run_instagram(args.url, args.count)
        elif args.platform == 'threads':
            run_threads(args.url, args.count)
        elif args.platform == 'tiktok':
            run_tiktok(args.url, args.count)
        elif args.platform == 'twitter':
            run_twitter(args.url, args.count)

if __name__ == "__main__":
    main()