from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import lxml.html
import re

import mistune

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


class PangoRenderer(mistune.Renderer):
    '''
    Pango Markdown renderer

    See also
    --------
    `markdown2pango()`
    '''
    def __init__(self, **kwargs):
        self.options = kwargs

    def block_code(self, code, lang=None):
        code = code.rstrip('\n')
        return '<tt>%s</tt>\n' % code

    def block_quote(self, text):
        return text

    def header(self, text, level, raw=None):
        if level >= 1 and level < 4:
            size = ('xx-large', 'x-large', 'large')[level - 1]
            return "<span size='%s' font_weight='bold'>%s</span>\n\n" % (size,
                                                                         text)
        return text + '\n\n'

    def hrule(self):
        return '\n%s\n' % (72 * '-')

    def paragraph(self, text):
        return '\n%s\n' % text.strip()

    def double_emphasis(self, text):
        return '<b>%s</b>' % text

    def emphasis(self, text):
        return '<i>%s</i>' % text

    def codespan(self, text):
        text = mistune.escape(text.rstrip(), smart_amp=False)
        return '<tt>%s</tt>' % text

    def linebreak(self):
        return '\n'

    def strikethrough(self, text):
        return '<s>%s</s>' % text

    def newline(self):
        """Rendering newline element."""
        return ''


def markdown2pango(markdown_text):
    '''
    Render Markdown-formatted text as Pango formatted text.

    Note
    ----
    Pango does not fully support _all_ markdown styles (e.g., lists).  In most
    cases, some attempt has been made to render something sensible (e.g.,
    render unordered list items with leading ``-``, ordered list items with
    item number, etc.).

    Parameters
    ----------
    markdown_text : str
        Markdown-formatted text.

    Returns
    -------
    str
        `Pango markup <https://developer.gnome.org/pango/stable/PangoMarkupFormat.html>`_.
    '''
    def sub_list(match):
        '''
        Substitute root level HTML lists with Markdown list
        '''
        def extract_list_items(root, level=0):
            content = []

            for list_i in root.xpath('ul|ol'):
                for j, child_ij in enumerate(list_i.xpath('li')):
                    leader_ij = '-' if list_i.tag == 'ul' else '%d.' % (j + 1)
                    subcontent_ij = extract_list_items(child_ij,
                                                       level=level + 1)
                    child_ij.text = ' %s%s %s' % ('  ' * level, leader_ij,
                                                  child_ij.text
                                                  if child_ij.text else '')
                    content += [(level, child_ij)]
                    content.extend(subcontent_ij)
                if root.tag != 'body':
                    root.remove(list_i)
                else:
                    list_i.drop_tag()
            return content

        root = lxml.html.fragment_fromstring(match.group())

        items = extract_list_items(root.xpath('/html/body')[0])

        output = ''

        for level, item in items:
            item_str = re.sub(r'^<li>(.*)</li>', r'\1',
                              lxml.html.tostring(item))
            output += item_str

        return output.rstrip('\n')

    m = mistune.Markdown(renderer=PangoRenderer())
    return re.sub(r'^<ul>.*</ul>', sub_list, m.render(markdown_text),
                  flags=re.DOTALL | re.MULTILINE)
