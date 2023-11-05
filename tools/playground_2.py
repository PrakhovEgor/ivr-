import re
a = "fdghdfh.[2][1gfhgfh2]"
re.sub(r'\[.*?\]', '', a)

print(re.sub(r'\[.*?\]', '', a))