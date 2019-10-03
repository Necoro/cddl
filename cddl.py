#!/usr/bin/python3
# ------------------------------------------------------------------------------
# Set download path etc...
downLoadPath  = '/your/download/directory'
zugangsNummer = '012345678' # see also -l option
gotoArchive   = False # see also -a option
maxTimeout = 500 # max timeout in s

# ------------------------------------------------------------------------------
# Misc imports
import os, sys
import atexit
from optparse import OptionParser
from time import sleep
from getpass import getpass
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options

# ------------------------------------------------------------------------------
# Prepare and open the chrome driver
def cddlDriver():
    chromeOptions = Options()
    chromeOptions.add_experimental_option('prefs',  {
        "download.default_directory":         downLoadPath,
        "download.prompt_for_download":       False,
        "download.directory_upgrade":         True,
        "plugins.always_open_pdf_externally": True
        }
    )
    return webdriver.Chrome('/usr/bin/chromedriver', chrome_options = chromeOptions)

# Graceful shutdown
def cddlClose(driver):
    driver.quit()

# Busy waiting for element
def waitFor(driver, condition, descr):
    try:
        return WebDriverWait(driver, maxTimeout).until(condition)
    except TimeoutException:
        print('Encountered Timeout during waiting for {}. Perhaps increase the timeout (current value: {:d}).'.format(descr, maxTimeout))
        sys.exit(2)

# Login and goto postbox
def cddlLogin(driver, loginDirectly=False, gotoArchive=False):
    comdirectUrl  = 'https://kunde.comdirect.de/lp/wt/login?execution=e1s1&afterTimeout=true'
    postBoxUrl    = 'https://kunde.comdirect.de/itx/posteingangsuche'
    driver.get(comdirectUrl);

    # Get the elements
    zugangsNummerField  = driver.find_element_by_name('param1')
    pinField            = driver.find_element_by_name('param3')
    loginButton         = driver.find_element_by_id('loginAction')

    # Login
    zugangsNummerField.send_keys(zugangsNummer)
    if not loginDirectly:
        pinField.send_keys(getpass('PIN: '))
        loginButton.click()
        sleep(1)
    else:
        # Necoro: one could use url_contains here, but this is not supported by my version of selenium
        waitFor(driver, EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, 'PostBox')), 'login')

    # Goto postbox
    driver.get(postBoxUrl)
    waitFor(driver, EC.presence_of_element_located((By.LINK_TEXT, 'Archiv')), 'postbox')

    # Enable this if you want to go to the archive
    if gotoArchive:

        # Find Archiv button
        archivLink = driver.find_element_by_link_text('Archiv')
        archivLink.click()

        # Select GESAMTER_ZEITRAUM
        zeitraumSelect = driver.find_element_by_id('f1-zeitraumInput_pbInput')
        selectField    = webdriver.support.ui.Select(zeitraumSelect)
        selectField.select_by_value('GESAMTER_ZEITRAUM')

        # Start search
        suchenField = driver.find_element_by_link_text('Suchen')
        suchenField.click()

    return driver

# ------------------------------------------------------------------------------
# Download PDF files
def cddlGetPdf(driver):

    # Reset counters
    cntPdf  = 0
    cntHtml = 0
    page    = 0

    while True:

        page = page + 1
        print('----------------------------------------------')
        print('Downloading page {:d}'.format(page))
        print()

        # Scroll down to show the page number
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        sleep(1)

        # Get links and extract direct PDF-URLs from the links
        pdfLinks = driver.find_elements_by_css_selector("a[id*='urlAbfrage'][href*='.pdf']")
        pdfUrls  = []
        for pdfLink in pdfLinks:
            pdfUrls.append(pdfLink.get_attribute("href"))

        # Get the HTML links
        htmlLinks = driver.find_elements_by_css_selector("a[id*='urlAbfrage'][href*='.html']")
        htmlUrls  = []
        for htmlLink in htmlLinks:
            htmlUrls.append(htmlLink.get_attribute("href"))

        # Download all the PDFs to the default directory
        error = False
        for pdfUrl in pdfUrls:
            try:
                # Get short URL -> use part after last '/', use part before '?'
                pdfUrlShort = (pdfUrl.split('/')[-1]).split('?')[0]

                # Sometimes, Termingebundenes is .pdf despite being HTML -> check
                x = pdfUrl.split('Termingebundenes');
                if len(x) == 1:                         # Normal PDF download
                    cntPdf = cntPdf + 1
                    driver.get(pdfUrl)
                    sleep(0.1)
                    print('Get  {:4d}: {:s}'.format(cntPdf, pdfUrlShort))
                else:                                   # Skip possibly HTML
                    cntHtml = cntHtml + 1
                    print('Skip {:4d}: {:s}'.format(cntHtml, pdfUrlShort))
            except:
                driver.back()
                print('Error, failed to load {:s}'.format(pdfUrlShort))
                error = True
                break

        # Go to the next page
        if not error:

            # Show how many URLS were skipped
            for htmlUrl in htmlUrls:
                cntHtml = cntHtml + 1
                x = htmlUrl.split('/');
                htmlUrlShort = x[-1]
                print('Skip {:4d}: {:s}'.format(cntHtml, htmlUrlShort))
            print()

            # Check if there is another right button - stop if not
            try:
                rightbutton = driver.find_element_by_css_selector("a[id='f1-j_idt123_right']")
            except:
                print('----------------------------------------------')
                print('Downloaded -> {:5d} documents'.format(cntPdf))
                print('Skipped    -> {:5d} documents'.format(cntHtml))
                print('No more right button -> End of download')
                print('----------------------------------------------')
                if os.environ.get('PYTHONINSPECT'):
                    print()
                    print('You are now in interactive mode!')
                    print('-> You can navigate the browser at your will.')
                    print('-> Enter >cddlGetPdf(drv)< to download the pdfs from the current view.')
                    print('-> Enter >exit()< or press Ctrl-D to exit.')
                break;
            driver.execute_script("arguments[0].click();", rightbutton)

        # Stop on error
        else:
            break

# ------------------------------------------------------------------------------
def enable_inspect():
    # force interactive mode
    os.environ["PYTHONINSPECT"] = 'x'

# Login and download
if __name__ == "__main__":
    opt = OptionParser()
    opt.add_option('-i', action="callback", callback=enable_inspect, help="Enable interactive mode")
    opt.add_option('-l', action="store_true", dest="login", help="Login directly in browser")
    opt.add_option('-a', action="store_true", dest="archive", help="Goto archive instead of main postbox")

    options, _ = opt.parse_args()

    drv = cddlDriver()

    # quit driver on exit
    atexit.register(cddlClose, drv)

    cddlLogin(drv, options.login, options.archive or gotoArchive)
    cddlGetPdf(drv)

# ------------------------------------------------------------------------------
