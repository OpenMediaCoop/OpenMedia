# For now, hardcoded configs. Later can load from site manager
def site_configs():
    """Load site configurations for Chilean news sites."""
    return {
        'emol': {
            'name': 'El Mercurio Online',
            'domain': 'emol.com',
            'homepage': 'https://www.emol.com/noticias/',
            'article_pattern': r'/noticias/[^/]+/\d{4}/\d{2}/\d{2}/\d+/',
            'selectors': {
                'article_links': 'a[href*="/noticias/"]',
                'title': 'h1#cuDetalle_cuTitular_tituloNoticia',
                'subtitle': 'h2#cuDetalle_cuTitular_bajadaNoticia',
                'content': 'div#cuDetalle_cuTexto_textoNoticia',
                'author': 'div.info-notaemol-porfecha',
                'date': 'meta[property="article:published_time"]',
                # Metadatos del <head>
                'meta_title': 'title',
                'meta_description': 'meta[name="description"]',
                'meta_keywords': 'meta[name="keywords"]',
                'meta_author': 'meta[name="author"]',
                'canonical_url': 'link[rel="canonical"]',
                # Open Graph
                'og_title': 'meta[property="og:title"]',
                'og_description': 'meta[property="og:description"]',
                'og_image': 'meta[property="og:image"]',
                'og_url': 'meta[property="og:url"]',
                'og_site_name': 'meta[property="og:site_name"]',
                # Twitter Cards
                'twitter_title': 'meta[name="twitter:title"]',
                'twitter_description': 'meta[name="twitter:description"]',
                'twitter_image': 'meta[name="twitter:image"]',
                'twitter_card': 'meta[name="twitter:card"]',
                # JSON-LD structured data
                'json_ld': 'script[type="application/ld+json"]'
            }
        },
        'latercera': {
            'name': 'La Tercera',
            'domain': 'latercera.com',
            'homepage': 'https://www.latercera.com/',
            'article_pattern': r'/noticia/',
            'use_json_ld': True,  # Priorizar JSON-LD
            'selectors': {
                'article_links': 'a[href*="/noticia/"]',
                'title': 'h1.article-head__title',
                'subtitle': 'h2.article-head__subtitle',
                'content': 'main.article-right-rail__main',
                'content_paragraphs': 'p.article-body__paragraph',
                'author': 'span.article-body__byline__authors',
                'author_link': 'a.article-body__byline__author',
                'date': 'time.article-body__byline__date',
                # Metadatos del <head>
                'meta_title': 'title',
                'meta_description': 'meta[name="description"]',
                'meta_keywords': 'meta[name="keywords"]',
                'meta_author': 'meta[name="author"]',
                'canonical_url': 'link[rel="canonical"]',
                # Open Graph
                'og_title': 'meta[property="og:title"]',
                'og_description': 'meta[property="og:description"]',
                'og_image': 'meta[property="og:image"]',
                'og_url': 'meta[property="og:url"]',
                'og_site_name': 'meta[property="og:site_name"]',
                # Twitter Cards
                'twitter_title': 'meta[name="twitter:title"]',
                'twitter_description': 'meta[name="twitter:description"]',
                'twitter_image': 'meta[name="twitter:image"]',
                'twitter_card': 'meta[name="twitter:card"]',
                # JSON-LD structured data
                'json_ld': 'script[type="application/ld+json"]'
            }
        },
        'biobio': {
            'name': 'BioBio Chile',
            'domain': 'biobiochile.cl',
            'homepage': 'https://www.biobiochile.cl/',
            'article_pattern': r'/noticias/',
            'use_json_ld': True,  # Priorizar JSON-LD como La Tercera
            'selectors': {
                'article_links': 'a[href*="/noticias/"]',
                # Selectores principales de contenido
                'title': 'h1',
                'subtitle': 'h2.bajada',
                'content': '.post .post-content',  # Contenedor principal del artículo
                'content_paragraphs': '.post .post-content p',  # Párrafos específicos
                'author': '.autores',  # Selector específico para autores
                'author_link': '.autores a',  # Enlaces de autor si existen
                'date': 'time',
                'date_published': 'meta[itemprop="datePublished"]',  # Microdatos
                'date_modified': 'meta[itemprop="dateModified"]',
                
                # Elementos específicos de BioBio
                'article_id': 'meta[name="identrada"]',  # ID interno de la nota
                'article_section': 'meta[itemprop="articleSection"]',  # Sección del artículo
                'destacador': '.destacador',  # Frases destacadas
                'lee_tambien': '.lee-tambien-bbcl',  # Secciones "Leer también"
                'wp_caption': '.wp-caption',  # Leyendas de imágenes
                'audio_elements': '.wp-audio-shortcode',  # Elementos de audio
                
                # Metadatos del <head>
                'meta_title': 'title',
                'meta_description': 'meta[name="description"]',
                'meta_keywords': 'meta[name="keywords"]',
                'meta_news_keywords': 'meta[name="news_keywords"]',  # Keywords específicas de noticias
                'meta_author': 'meta[name="author"]',
                'canonical_url': 'link[rel="canonical"]',
                'amp_url': 'link[rel="amphtml"]',  # URL de versión AMP
                
                # Open Graph (Facebook)
                'og_title': 'meta[property="og:title"]',
                'og_description': 'meta[property="og:description"]',
                'og_image': 'meta[property="og:image"]',
                'og_url': 'meta[property="og:url"]',
                'og_site_name': 'meta[property="og:site_name"]',
                'og_type': 'meta[property="og:type"]',
                'og_article_author': 'meta[property="article:author"]',
                'og_article_section': 'meta[property="article:section"]',
                'og_article_published_time': 'meta[property="article:published_time"]',
                'og_article_modified_time': 'meta[property="article:modified_time"]',
                
                # Twitter Cards
                'twitter_title': 'meta[name="twitter:title"]',
                'twitter_description': 'meta[name="twitter:description"]',
                'twitter_image': 'meta[name="twitter:image"]',
                'twitter_card': 'meta[name="twitter:card"]',
                'twitter_site': 'meta[name="twitter:site"]',
                'twitter_creator': 'meta[name="twitter:creator"]',
                
                # Facebook específicos
                'fb_pages': 'meta[property="fb:pages"]',
                'fb_app_id': 'meta[property="fb:app_id"]',
                'fb_admins': 'meta[property="fb:admins"]',
                
                # Favicons y Apple Touch Icons
                'favicon': 'link[rel="icon"]',
                'apple_touch_icon': 'link[rel="apple-touch-icon"]',
                
                # JSON-LD structured data
                'json_ld': 'script[type="application/ld+json"]',
                
                # Atributos de datos específicos
                'data_id_nota': 'head[data-id-nota]'  # ID de nota desde atributo data
            }
        }
    }

sites = site_configs()