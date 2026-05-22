#!/usr/bin/env bash
cd "$(dirname "$0")"

./webflow_transtype.py
./webflow_fontlab_8.py
./webflow_fontlab_home.py
./webflow_retro_poster.py
./mkdocs_blog_post.py
