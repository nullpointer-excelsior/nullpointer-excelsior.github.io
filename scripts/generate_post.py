
from datetime import datetime


def generate_filename(title: str, path: str = None):
    path_file=f"{path + '/' if path is not None else ''}"
    return f"{path_file}{datetime.now().strftime('%Y-%m-%d')}-{title.lower().replace(' ', '-')}.md"


def create_post_file(title, categories, content:str, path=None):
    categories_text = str(categories).replace("'", "")
    tags = categories_text.lower()

    template=f"""
---
title: {title}
author: Benjamin
date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -0500
categories: {categories_text}
tags: {tags}
---

![img](imagen_post)

{content}

## [Github repository](url_repositorio)

Meme de cortesía

![meme](imagen_meme)
    """
    filename = generate_filename(title)
    with open(filename, "w") as file:
        file.write(template)



title="Como Implementar Clean Arquitecture en el Frontend"
categories=["Frontend", "React", "Rxjs", "Arquitectura Frontend", "Javascript", "Typescript"]
create_post_file(title=title, categories=categories, content="""
# Post de pruebas
lorem ipsum y la wea...
""")