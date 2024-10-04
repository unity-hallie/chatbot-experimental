import pyperclip


def main():
    # Get the current text from the clipboard
    input_text = pyperclip.paste()

    # Split the text into words
    words = input_text.split()

    # Extract every third word
    third_words = words[4::5]  # Start at index 2 and take every third word

    # Join the third words back into a single string
    output_text = ' '.join(third_words)

    # Copy the output text back to the clipboard
    pyperclip.copy(output_text)

    print("Every third word has been copied back to the clipboard.")


if __name__ == "__main__":
    main()
