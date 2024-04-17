from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import customtkinter as ctk
import threading
import requests
from PIL import Image
from pypdf import PdfWriter
from io import BytesIO
import re
import os

options = Options()
options.add_argument("--headless=new")
root = ctk.CTk()


def main():
    # Get the directory of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the paths to icon.ico relative to the script directory
    icon_path = os.path.join(script_dir, "icon.ico")

    # set the GUI of the app
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    root.title("Manga Downloader")
    root.iconbitmap(icon_path)
    root.geometry("720x480")
    content_frame = ctk.CTkFrame(root)
    content_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

    # URL input
    url_label = ctk.CTkLabel(content_frame, text="↓↓↓ Enter the Manga link here ↓↓↓")
    entry_url = ctk.CTkEntry(content_frame, width=400, height=40)
    url_label.pack(pady=(10, 5))
    entry_url.pack(pady=(10.5))

    # look for chapters
    available_label = ctk.CTkLabel(content_frame)
    entry_from = ctk.CTkEntry(content_frame, width=200, height=25)

    entry_to = ctk.CTkEntry(content_frame, width=200, height=25)
    entry_title = ctk.CTkEntry(content_frame, width=200, height=25)

    status_label = ctk.CTkLabel(content_frame)
    progress_bar = ctk.CTkProgressBar(content_frame, width=400)
    download_button = ctk.CTkButton(
        content_frame,
        text="Download chapters",
    )

    chapters_button = ctk.CTkButton(
        content_frame,
        text="Look for chapters",
        command=lambda: threading.Thread(
            target=get_chapters,
            args=(
                entry_url.get(),
                available_label,
                entry_from,
                entry_to,
                entry_title,
                status_label,
                progress_bar,
                download_button,
            ),
        ).start(),
    )

    chapters_button.pack(pady=(10, 5))

    # change the appearance of the GUI
    light_mode_button = ctk.CTkButton(
        content_frame,
        text="Light mode",
        command=lambda: ctk.set_appearance_mode("light"),
    )
    light_mode_button.place(relx=0.29, rely=0.99, anchor="s")
    system_mode_button = ctk.CTkButton(
        content_frame,
        text="Same as system",
        command=lambda: ctk.set_appearance_mode("system"),
    )
    system_mode_button.place(relx=0.5, rely=0.99, anchor="s")
    dark_mode_button = ctk.CTkButton(
        content_frame, text="Dark mode", command=lambda: ctk.set_appearance_mode("dark")
    )
    dark_mode_button.place(relx=0.71, rely=0.99, anchor="s")

    # run the app
    root.mainloop()


def get_chapters(
    url,
    available_label,
    entry_from,
    entry_to,
    entry_title,
    status_label,
    progress_bar,
    download_button,
):
    try:
        # forget UI elements from previus downloads
        try:
            available_label.pack_forget()
            entry_title.pack_forget()
            entry_from.pack_forget()
            entry_to.pack_forget()
            download_button.pack_forget()
            status_label.pack_forget()
            progress_bar.pack_forget()
        except Exception as e:
            print(e)

        available_label.configure(text="Looking for chapters...")
        available_label.pack(pady=(10, 5))

        driver = webdriver.Chrome(options=options)
        # open the link with the driver
        driver.get(url)

        try:
            # wait for the button to be clickable
            all_chapters_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "div.list-group-item.ShowAllChapters.ng-scope")
                )
            )
            # Click on the "Show All Chapters" button
            all_chapters_button.click()
        except:
            pass

        # Get all chapter links
        WebDriverWait(driver, 1).until(
            EC.visibility_of_all_elements_located(
                (By.CSS_SELECTOR, "a.list-group-item.ChapterLink.ng-scope")
            )
        )
        chapter_elements = driver.find_elements(
            By.CSS_SELECTOR, "a.list-group-item.ChapterLink.ng-scope"
        )
        available_chapters = len(chapter_elements)

        # chapters available
        chapters = list(range(1, available_chapters + 1))
        available_label.configure(
            text=f"Available chapters: {chapters[0]} - {chapters[len(chapters) - 1]}"
        )

        # download chapters
        entry_from.delete(0, "end")  # Delete all characters from index 0 to the end
        entry_title.delete(0, "end")
        entry_to.delete(0, "end")
        entry_from.configure(placeholder_text="from")  # configure the placeholder text
        entry_title.configure(placeholder_text="Title")
        entry_to.configure(placeholder_text="to")
        entry_title.pack(pady=(10, 5))
        entry_from.pack(pady=(10, 5))
        entry_to.pack(pady=(10, 5))
        download_button.pack(pady=(10, 5))
        download_button.configure(
            command=lambda: threading.Thread(
                target=manga_downloader,
                args=(
                    entry_title.get(),
                    int(entry_from.get()),
                    int(entry_to.get()),
                    chapter_elements,
                    driver,
                    status_label,
                    progress_bar,
                ),
            ).start(),
        )
    except Exception as e:
        available_label.configure(text=e)
        raise e


def manga_downloader(
    title,
    chapter_from,
    chapter_to,
    chapter_elements,
    driver,
    status_label,
    progress_bar,
):
    try:
        chapter_links = []
        for chapter_element in chapter_elements:
            number = int(re.search(r"(\d+(?:\.\d+)?)", chapter_element.text).group(1))
            if chapter_from <= number <= chapter_to:
                chapter_links.append(chapter_element.get_attribute("href"))

        # Create a directory to save the PDFs
        os.makedirs(title, exist_ok=True)
        total = len(chapter_links)
        status_label.configure(text=f"Chapters downloaded: 0 of {total}")
        status_label.pack(pady=(10, 5))
        progress_bar.set(0)
        progress_bar.pack(pady=(10, 5))

        # go to each chapter link
        for i, chapter_link in enumerate(chapter_links):
            download_chapter(driver, chapter_link, title)
            status_label.configure(text=f"Chapters downloaded: {i + 1} of {total}")
            progress_bar.set(float((i + 1) / total))
    except Exception as e:
        status_label.configure(text=e)
        driver.quit()
        raise e

    driver.quit()
    status_label.configure(text=f"Download complete")


def download_chapter(driver, chapter_link, title):
    driver.get(chapter_link)
    try:
        # Find the "Long Strip" button
        long_strip_button = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[contains(@class, 'btn') and contains(@class, 'btn-sm') and contains(@class, 'btn-outline-secondary') and contains(@class, 'ng-binding') and contains(., 'Long Strip')]",
                )
            )
        )

        # Click the "Long Strip" button
        long_strip_button.click()
    except:
        # If the button does not exist, pass
        pass

    # find all the images from a chapter
    image_elements = driver.find_elements(
        By.XPATH,
        '//img[contains(@class, "img-fluid") and contains(@class, "HasGap")]',
    )
    chapter_number = driver.find_element(
        By.XPATH,
        '//button[contains(@class, "btn btn-sm") and contains(@class, "btn-outline-secondary") and contains(@class, "ng-binding")]',
    ).text.strip()

    pdf_writer = PdfWriter()

    # Download and save each image
    for image_element in image_elements:
        image_url = image_element.get_attribute("src")
        response = requests.get(image_url)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            # Convert the image to RGB format if it's not already in RGB
            if image.mode != "RGB":
                image = image.convert("RGB")  # Append the image to the PDF
            with BytesIO() as f:
                image.save(f, format="pdf")
                pdf_writer.append(f)
        else:
            return SystemError

    # Write the PDF to disk in the specified directory
    output_pdf_path = os.path.join(title, f"{chapter_number}.pdf")
    with open(output_pdf_path, "wb") as f:
        pdf_writer.write(f)


if __name__ == "__main__":
    main()
