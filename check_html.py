with open("output/web/viewer.html", encoding="utf-8") as f:
    content = f.read()
print("Has DATA object:", "__DATA__" not in content)
print("Has NAV html:   ", "__NAV__" not in content)
print("Para count:     ", content.count('class="para"'))
print("Seg count:      ", content.count('class="seg '))
