from read_transcript import read_transcript
from find_decisions import find_decisions

if __name__ == "__main__":

    file_path = "./tests/prod_start_meet.txt"
    transcript_entries = read_transcript(file_path)

    parsed_entries = find_decisions(transcript_entries)
    
    for entry in parsed_entries:
        if entry['type'] != 'none':
            if entry['type'] == 'decision':
                print(f"Decision found at {entry['timestamp']} by {entry['speaker']}: {entry['decision']}") 
            elif entry['type'] == 'action_item':
                print(f"Action item found at {entry['timestamp']} by {entry['speaker']}: {entry['action_item']}")
            else:
                print(f"Entry at {entry['timestamp']} by {entry['speaker']} has unknown type.")
            print(f"{'-'*40}")