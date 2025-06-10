import os
import re
from typing import Dict, List, Optional


def print_colored(text: str, color: str) -> None:
    """Prints colored text to the console."""
    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "blue": "\033[94m",
        "yellow": "\033[93m",
        "cyan": "\033[96m",
        "magenta": "\033[95m",
    }
    color_code = colors.get(color.lower(), "\033[0m")
    print(f"{color_code}{text}\033[0m")


def sanitize_filename(name: str) -> str:
    """
    Takes a string and returns a safe filename version, appending .m3u.
    Example: "USA: Sports (HD)" -> "USA_Sports_HD.m3u"
    """

    name = name.replace(" ", "_").replace(":", "-").replace("|", "-")

    name = re.sub(r"[^\w-]", "", name)
    return f"{name}.m3u"


def select_m3u_file() -> Optional[str]:
    """
    Scans the current directory for M3U files and prompts the user to select one.
    """
    try:
        m3u_files = [f for f in os.listdir(".") if f.endswith((".m3u", ".m3u8"))]
        if not m3u_files:
            print_colored(
                "No M3U files (.m3u, .m3u8) found in the current directory.", "red"
            )
            return None

        print_colored("Please select an M3U file to process:", "yellow")
        for i, filename in enumerate(m3u_files, 1):
            print(f"  [{i}] {filename}")

        while True:
            choice_str = input(f"\nEnter the number of the file (1-{len(m3u_files)}): ")
            choice = int(choice_str)
            if 1 <= choice <= len(m3u_files):
                return m3u_files[choice - 1]
            else:
                print_colored(
                    f"Invalid choice. Please enter a number between 1 and {len(m3u_files)}.",
                    "red",
                )
    except (ValueError, KeyboardInterrupt, EOFError):
        print_colored("\nSelection cancelled or invalid input. Exiting.", "yellow")
    return None


def get_extraction_mode() -> str:
    """Asks the user if they want to combine files or keep them separate."""
    while True:
        choice = input(
            "Save matching groups as (s)eparate files or (c)ombined into one? [s/c]: "
        ).lower()
        if choice in ["s", "separate"]:
            return "separate"
        if choice in ["c", "combined"]:
            return "combined"
        print_colored("Invalid choice. Please enter 's' or 'c'.", "red")


def extract_groups_by_query(m3u_path: str, query: str, mode: str) -> None:
    """
    Parses an M3U file and extracts channels based on a group title query and the selected mode.
    """
    print_colored(f"\nScanning '{m3u_path}' for groups containing '{query}'...", "cyan")

    groups_for_separate_files: Dict[str, List[str]] = {}
    channels_for_combined_file: List[str] = []

    query_lower = query.lower()

    try:
        with open(m3u_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception as e:
        print_colored(f"Could not read file. Error: {e}", "red")
        return

    total_channels_found = 0
    for i, line in enumerate(lines):
        if line.startswith("#EXTINF"):
            match = re.search(r'group-title="([^"]+)"', line, re.IGNORECASE)
            if match:
                group_title = match.group(1)
                if query_lower in group_title.lower():
                    total_channels_found += 1
                    channel_info = line
                    stream_url = lines[i + 1] if (i + 1) < len(lines) else ""

                    if mode == "separate":
                        if group_title not in groups_for_separate_files:
                            groups_for_separate_files[group_title] = []
                        groups_for_separate_files[group_title].extend(
                            [channel_info, stream_url]
                        )
                    else:
                        channels_for_combined_file.extend([channel_info, stream_url])

    if total_channels_found == 0:
        print_colored("\nNo channels found in any group matching your query.", "yellow")
        return

    print_colored(
        f"\nFound {total_channels_found} total channel(s) in matching groups.", "green"
    )

    if mode == "separate":
        print_colored(
            f"Creating {len(groups_for_separate_files)} separate file(s)...", "green"
        )
        for group_title, channel_lines in groups_for_separate_files.items():
            output_filename = sanitize_filename(group_title)
            channel_count = len(channel_lines) // 2
            try:
                with open(output_filename, "w", encoding="utf-8") as f:
                    f.write("#EXTM3U\n")
                    f.writelines(channel_lines)
                print_colored(
                    f"  - Created '{output_filename}' with {channel_count} channels.",
                    "blue",
                )
            except IOError as e:
                print_colored(
                    f"Error writing file for group '{group_title}': {e}", "red"
                )

    else:
        output_filename = sanitize_filename(f"{query}_combined")
        print_colored("Creating combined file...", "green")
        try:
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                f.writelines(channels_for_combined_file)
            print_colored(
                f"  - Created '{output_filename}' with {total_channels_found} channels.",
                "blue",
            )
        except IOError as e:
            print_colored(f"Error writing combined file: {e}", "red")


def main():
    """Main function to drive the tool."""
    print_colored("--- M3U Group Extractor ---", "magenta")

    m3u_file = select_m3u_file()
    if not m3u_file:
        return

    print_colored(f"\nFile selected: '{m3u_file}'", "green")

    query = input("Enter the group name to search for (e.g., 'bein', 'sports', 'UK'): ")
    if not query.strip():
        print_colored("Error: Search query cannot be empty.", "red")
        return

    mode = get_extraction_mode()

    extract_groups_by_query(m3u_file, query, mode)


if __name__ == "__main__":
    main()
