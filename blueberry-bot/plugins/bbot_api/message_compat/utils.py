def escapeMarkdown(text:str):
    escapeCharactors="\\`[]*!#"
    for c in escapeCharactors:
        text=text.replace(c,"\\"+c)
    return text