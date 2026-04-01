from read_transcript import read_transcript
from find_decisions import find_decisions

if __name__ == "__main__":

    # file_path = input("Enter the path to the transcript file: ").strip()
    file_path = "./tests/prod_start_meet.txt"
    transcript_entries = read_transcript(file_path)

    parsed_entries = find_decisions(transcript_entries)
    
    for entry in parsed_entries:
        if entry['type'] != 'none':
            print(f"Content: {entry['content']}\nType: {entry['type']}\n Decision: {entry['decision']}\nAction Item: {entry['action_item']}\n{'-'*40}")