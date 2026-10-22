with open('app/core/tutoring_engine.py', 'r', encoding='utf-8') as f:
    text = f.read()

marker_start = '            # 7. MLFQ: Priority Boost / Starvation check question'
marker_end = '                    difficulty_level=learner_state.difficulty_level or "beginner",\n                    is_fallback=False\n                )'

stride_anchor = '            # 11. Stride Scheduling: Smaller stride check question'
stride_pos = text.find(stride_anchor)
end_pos = text.find(marker_end, stride_pos) + len(marker_end)
single_block = text[text.find(marker_start):end_pos]
print('Single block length:', len(single_block))

text_clean = text.replace(single_block, '')
print('Remaining occurrences:', text_clean.count(marker_start))

hrrn_anchor = '            # 6. HRRN: Response ratio check question'
hrrn_pos = text_clean.find(hrrn_anchor)
hrrn_end_pos = text_clean.find(marker_end, hrrn_pos) + len(marker_end)

final_text = text_clean[:hrrn_end_pos] + '\n\n' + single_block + text_clean[hrrn_end_pos:]
print('Final text length:', len(final_text), 'lines:', len(final_text.splitlines()))
print('Final occurrences of MLFQ check:', final_text.count(marker_start))

with open('app/core/tutoring_engine.py', 'w', encoding='utf-8') as f:
    f.write(final_text)
