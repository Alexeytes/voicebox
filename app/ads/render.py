def render_banner_html(banner):
    return f'<a href="/go/banner/{banner.id}" rel="noopener sponsored" target="_blank"><img src="{banner.image_url}" alt="{banner.alt_text}"></a>'
