use pyo3::prelude::*;
use pyo3::types::PyModule;

#[derive(Debug)]
enum Block<'a> {
    Header(u8, &'a str),
    ListItem(&'a str),
    BlockQuote(&'a str),
    HorizontalRule,
    Paragraph(&'a str),
    Empty,
}

impl<'a> From<&'a str> for Block<'a> {
    fn from(line: &'a str) -> Self {
        let trimmed = line.trim();
        if trimmed.is_empty() {
            return Block::Empty;
        }

        // Horizontal Rules
        if trimmed == "---" || trimmed == "***" || trimmed == "___" {
            return Block::HorizontalRule;
        }

        // Headers
        if trimmed.starts_with('#') {
            let hash_count = trimmed.chars().take_while(|&c| c == '#').count();
            if hash_count > 0 && hash_count <= 6 {
                let content = trimmed[hash_count..].trim();
                return Block::Header(hash_count as u8, content);
            }
        }

        // BlockQuotes
        if trimmed.starts_with("> ") {
            return Block::BlockQuote(&trimmed[2..]);
        }

        // List Items
        if trimmed.starts_with("- ") {
            return Block::ListItem(&trimmed[2..]);
        }

        Block::Paragraph(trimmed)
    }
}

fn parse_inlines(text: &str) -> String {
    let mut result = String::new();
    let mut chars = text.chars().peekable();

    let mut bold = false;
    let mut italic = false;
    let mut code = false;
    let mut strike = false;

    while let Some(c) = chars.next() {
        match c {
            '*' => {
                if chars.peek() == Some(&'*') {
                    chars.next(); // Consume second '*'
                    bold = !bold;
                    result.push_str(if bold { "<strong>" } else { "</strong>" });
                } else {
                    italic = !italic;
                    result.push_str(if italic { "<em>" } else { "</em>" });
                }
            }
            '`' => {
                code = !code;
                result.push_str(if code { "<code>" } else { "</code>" });
            }
            '~' => {
                if chars.peek() == Some(&'~') {
                    chars.next(); // Consume second '~'
                    strike = !strike;
                    result.push_str(if strike { "<del>" } else { "</del>" });
                } else {
                    result.push(c);
                }
            }
            '[' => {
                // Potential link start: [text](url)
                let mut text_buf = String::new();
                let mut found_closing_bracket = false;

                // 1. Capture text inside []
                while let Some(&next_c) = chars.peek() {
                    if next_c == ']' {
                        chars.next();
                        found_closing_bracket = true;
                        break;
                    }
                    text_buf.push(chars.next().unwrap());
                }

                // 2. Capture URL inside () if we found ] and next char is (
                if found_closing_bracket && chars.peek() == Some(&'(') {
                    chars.next(); // consume (
                    let mut url_buf = String::new();
                    let mut found_closing_paren = false;

                    while let Some(&next_c) = chars.peek() {
                        if next_c == ')' {
                            chars.next();
                            found_closing_paren = true;
                            break;
                        }
                        url_buf.push(chars.next().unwrap());
                    }

                    if found_closing_paren {
                        // Success: Render link
                        result.push_str(&format!(
                            "<a href=\"{}\" target=\"_blank\" rel=\"noopener noreferrer\">{}</a>",
                            url_buf, text_buf
                        ));
                    } else {
                        // Failed to find closing paren: backtrack
                        result.push('[');
                        result.push_str(&text_buf);
                        result.push(']');
                        result.push('(');
                        result.push_str(&url_buf);
                    }
                } else {
                    // Not a link: backtrack
                    result.push('[');
                    result.push_str(&text_buf);
                    if found_closing_bracket {
                        result.push(']');
                    }
                }
            }
            _ => result.push(c),
        }
    }
    result
}

#[pyfunction]
fn render_to_html(markdown: &str) -> PyResult<String> {
    let mut html = String::new();
    let mut in_list = false;

    for line in markdown.lines() {
        let block = Block::from(line);

        // Handle List State Transitions
        match (&block, in_list) {
            (Block::ListItem(_), false) => {
                html.push_str("<ul>\n");
                in_list = true;
            }
            (Block::ListItem(_), true) => {}
            (_, true) => {
                html.push_str("</ul>\n");
                in_list = false;
            }
            (_, false) => {}
        }

        // Render Blocks
        let rendered = match block {
            Block::Header(level, content) => {
                format!("<h{}>{}</h{}>", level, parse_inlines(content), level)
            }
            Block::ListItem(content) => {
                format!("<li>{}</li>", parse_inlines(content))
            }
            Block::BlockQuote(content) => {
                format!("<blockquote>{}</blockquote>", parse_inlines(content))
            }
            Block::HorizontalRule => String::from("<hr />"),
            Block::Paragraph(content) => {
                format!("<p>{}</p>", parse_inlines(content))
            }
            Block::Empty => String::new(),
        };

        if !rendered.is_empty() {
            html.push_str(&rendered);
            html.push('\n');
        }
    }

    if in_list {
        html.push_str("</ul>\n");
    }

    Ok(html)
}

#[pymodule]
fn markdown_render(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(render_to_html, m)?)?;
    Ok(())
}
