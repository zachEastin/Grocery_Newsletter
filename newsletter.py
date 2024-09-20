import bs4
import requests
from pathlib import Path
import datetime
import openai
import csv
import pandas as pd
from PIL import Image
import pytesseract
from dotenv import load_dotenv
from os import environ

load_dotenv()

OPENAIKEY = environ.get("OPENAIKEY")

# OpenAI API Key
openai.api_key = OPENAIKEY


# Function to extract text from image using pytesseract
def extract_text_from_image(image_path):
    try:
        # Load the image using PIL
        image = Image.open(image_path)

        # Use pytesseract to do OCR on the image
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return ""


# Function to use OpenAI to process extracted text
def process_text_with_openai(extracted_text):
    try:
        # Use OpenAI's GPT model to clean and structure the extracted text
        prompt = f"Here is the extracted text from a grocery store's weekly ad:\n\n'{extracted_text}'\n\nPlease organize this into food items and their corresponding deals in the format 'Food: Deal'."
        response = openai.Completion.create(
            engine="gpt-4", prompt=prompt, max_tokens=150
        )

        return response.choices[0].text.strip()

    except Exception as e:
        print(f"Error processing text with OpenAI: {e}")
        return ""


# Function to parse the structured output from OpenAI into food and deal pairs
def parse_text_to_food_deal(openai_response_text):
    food_deal_pairs = []
    lines = openai_response_text.split("\n")

    # Parse lines formatted as 'Food: Deal'
    for line in lines:
        if ":" in line:  # Assuming 'food : deal' pattern
            food, deal = line.split(":", 1)
            food = food.strip()
            deal = deal.strip()
            if food and deal:
                food_deal_pairs.append([food, deal])

    return food_deal_pairs


# Function to process all images in a directory and convert the results into a CSV
def process_images_to_csv(images: list[Path]):
    all_food_deal_data = []

    # Iterate over all image files in the given directory
    for image_path in images:
        # Extract text from image using pytesseract
        extracted_text = extract_text_from_image(image_path)

        # Use OpenAI to process and structure the extracted text
        structured_text = process_text_with_openai(extracted_text)

        # Parse text into structured food-deal pairs
        food_deal_pairs = parse_text_to_food_deal(structured_text)

        # Append the results to the list
        all_food_deal_data.extend(food_deal_pairs)

    # Convert the data into a DataFrame
    df = pd.DataFrame(all_food_deal_data, columns=["Food", "Deal"])

    # Save the DataFrame to a CSV file
    csv_path = images[0].parent / "deals.csv"
    df.to_csv(csv_path, index=False)
    print(f"CSV saved successfully at '{csv_path}'")


# Apple Market
def apple_market(force_download=False):
    url = "https://tcmarkets.com/location/ozark/"

    # Download all images in divs with class "weekly-ads"
    print("Opening Weekly Ad page...")
    soup = bs4.BeautifulSoup(requests.get(url).text, "html.parser")

    # Get all the images
    images = soup.select(".weekly-ads img")

    # Download all the images
    print("Downloading images...")
    image_paths = []
    for i, image in enumerate(images):
        image_url = image.attrs["src"]
        print(f"{i}/{len(images)}: {image_url}")

        image_name = image_url.split("/")[-1]
        today = datetime.datetime.today().strftime("%Y_%m_%d")
        image_path = Path("weekly_ad_images", today, "apple_market", image_name)

        if image_path.exists() and not force_download:
            print(f"  - Already Exists")
            continue

        image_path.parent.mkdir(parents=True, exist_ok=True)

        # Download the image to the current directory
        print(f"  - Downloading...", end="\r")
        with open(image_path, "wb") as file:
            file.write(requests.get(image_url).content)
        print(f"  - Downloaded          ")

        image_paths.append(image_path)
    print("Downloaded all images")

    # Generate a newsletter using OpenAI
    # openai.api_key = OPENAIKEY

    print("Generating deals...")
    process_images_to_csv(images)


apple_market(force_download=False)
