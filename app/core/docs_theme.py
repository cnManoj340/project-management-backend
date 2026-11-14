"""Custom look for the Swagger UI page served at /docs."""

DOCS_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
:root{
  --bg:#0b1020; --panel:#121a30; --panel2:#0e1529; --border:#25304f;
  --text:#e6e9f5; --muted:#93a0c4; --accent:#6366f1; --accent2:#22d3ee;
  --get:#38bdf8; --post:#34d399; --put:#fbbf24; --patch:#a78bfa; --delete:#f87171;
}
html,body{background:var(--bg)!important;}
body{font-family:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif!important;
  background:radial-gradient(900px 400px at 85% -5%,rgba(99,102,241,.22),transparent),
             radial-gradient(700px 350px at 0% 0%,rgba(34,211,238,.12),transparent),var(--bg)!important;}
.swagger-ui,.swagger-ui .info .title,.swagger-ui .info p,.swagger-ui .info li,.swagger-ui .info table,
.swagger-ui .opblock-tag,.swagger-ui .opblock .opblock-summary-description,.swagger-ui .opblock-description-wrapper p,
.swagger-ui .opblock-external-docs-wrapper p,.swagger-ui .opblock-title_normal p,.swagger-ui .tab li,
.swagger-ui .response-col_status,.swagger-ui .response-col_description,.swagger-ui .parameter__name,
.swagger-ui .parameter__type,.swagger-ui table thead tr th,.swagger-ui table thead tr td,
.swagger-ui .responses-inner h4,.swagger-ui .responses-inner h5,.swagger-ui label,.swagger-ui .model,
.swagger-ui .model-title,.swagger-ui section.models h4,.swagger-ui .opblock-summary-path,
.swagger-ui .opblock-summary-path__deprecated,.swagger-ui .dialog-ux .modal-ux-header h3,
.swagger-ui .dialog-ux .modal-ux-content h4,.swagger-ui .dialog-ux .modal-ux-content p,
.swagger-ui .markdown p,.swagger-ui .renderedMarkdown p,.swagger-ui .prop-type,.swagger-ui .prop-format,
.swagger-ui .servers>label{color:var(--text)!important;font-family:'Inter',sans-serif;}
.swagger-ui .info{margin:40px 0 24px;}
.swagger-ui .info .title{font-size:34px;font-weight:700;letter-spacing:-.02em;
  background:linear-gradient(90deg,#fff,#a5b4fc 60%,var(--accent2));-webkit-background-clip:text;
  background-clip:text;-webkit-text-fill-color:transparent;}
.swagger-ui .info .title small{background:var(--accent);border-radius:999px;padding:2px 10px;top:-4px;}
.swagger-ui .info .title small pre{color:#fff!important;-webkit-text-fill-color:#fff;}
.swagger-ui .info p,.swagger-ui .markdown p{color:var(--muted)!important;}
.swagger-ui .info a,.swagger-ui a{color:var(--accent2);}
.swagger-ui .wrapper{max-width:1200px;}

/* Authorize bar */
.swagger-ui .scheme-container{background:var(--panel)!important;border:1px solid var(--border);
  border-radius:14px;box-shadow:none!important;margin:0 0 24px;padding:16px 20px;}
.swagger-ui .btn{border-radius:10px;font-weight:600;box-shadow:none;transition:.15s;}
.swagger-ui .btn.authorize{color:#fff;background:linear-gradient(135deg,var(--accent),#8b5cf6);
  border:0;padding:8px 18px;}
.swagger-ui .btn.authorize svg{fill:#fff;}
.swagger-ui .btn.authorize:hover{filter:brightness(1.12);transform:translateY(-1px);}
.swagger-ui .btn.execute{background:var(--accent);border-color:var(--accent);color:#fff;}
.swagger-ui .btn.cancel{color:var(--delete);border-color:var(--delete);}
.swagger-ui .btn.try-out__btn{color:var(--accent2);border-color:var(--accent2);}
.swagger-ui .btn.btn-clear{color:var(--muted);}

/* Tag headers */
.swagger-ui .opblock-tag{font-size:20px;font-weight:600;border-bottom:1px solid var(--border)!important;
  padding:14px 8px;margin-top:10px;}
.swagger-ui .opblock-tag:hover{background:rgba(99,102,241,.08);}
.swagger-ui .opblock-tag small{color:var(--muted)!important;}
.swagger-ui .expand-operation svg,.swagger-ui .opblock-tag svg{fill:var(--muted);}

/* Operation blocks */
.swagger-ui .opblock{border-radius:12px;border-width:1px;box-shadow:none;margin:0 0 10px;}
.swagger-ui .opblock .opblock-summary{padding:6px 10px;}
.swagger-ui .opblock .opblock-summary-method{border-radius:8px;font-weight:700;min-width:74px;
  font-family:'JetBrains Mono',monospace;font-size:12px;color:#06101f;text-shadow:none;}
.swagger-ui .opblock .opblock-summary-path{font-family:'JetBrains Mono',monospace;font-size:14px;}
.swagger-ui .opblock.opblock-get{background:rgba(56,189,248,.07);border-color:rgba(56,189,248,.45);}
.swagger-ui .opblock.opblock-get .opblock-summary-method{background:var(--get);}
.swagger-ui .opblock.opblock-post{background:rgba(52,211,153,.07);border-color:rgba(52,211,153,.45);}
.swagger-ui .opblock.opblock-post .opblock-summary-method{background:var(--post);}
.swagger-ui .opblock.opblock-put{background:rgba(251,191,36,.07);border-color:rgba(251,191,36,.45);}
.swagger-ui .opblock.opblock-put .opblock-summary-method{background:var(--put);}
.swagger-ui .opblock.opblock-patch{background:rgba(167,139,250,.08);border-color:rgba(167,139,250,.5);}
.swagger-ui .opblock.opblock-patch .opblock-summary-method{background:var(--patch);}
.swagger-ui .opblock.opblock-delete{background:rgba(248,113,113,.07);border-color:rgba(248,113,113,.45);}
.swagger-ui .opblock.opblock-delete .opblock-summary-method{background:var(--delete);}
.swagger-ui .opblock .opblock-section-header{background:var(--panel2);box-shadow:none;
  border-bottom:1px solid var(--border);}
.swagger-ui .opblock .opblock-section-header h4{color:var(--text)!important;}
.swagger-ui .opblock-body{background:transparent;}
.swagger-ui .opblock-summary-control:focus{outline:none;}

/* Inputs & tables */
.swagger-ui input[type=text],.swagger-ui input[type=password],.swagger-ui input[type=search],
.swagger-ui input[type=email],.swagger-ui input[type=file],.swagger-ui textarea,.swagger-ui select{
  background:#0a1226!important;color:var(--text)!important;border:1px solid var(--border)!important;
  border-radius:8px;font-family:'JetBrains Mono',monospace;}
.swagger-ui input:focus,.swagger-ui textarea:focus,.swagger-ui select:focus{
  outline:none;border-color:var(--accent)!important;box-shadow:0 0 0 3px rgba(99,102,241,.25);}
.swagger-ui .filter .operation-filter-input{border-radius:10px;padding:10px 14px;margin:14px 0;}
.swagger-ui table tbody tr td{border-bottom:1px solid var(--border);color:var(--text);}
.swagger-ui .parameter__name.required span{color:var(--delete);}
.swagger-ui .parameter__in,.swagger-ui .parameter__extension{color:var(--muted)!important;}
.swagger-ui .response-col_links{color:var(--muted);}
.swagger-ui .responses-table .response-col_description__inner p{color:var(--muted)!important;}

/* Code blocks */
.swagger-ui .highlight-code>.microlight,.swagger-ui .opblock-body pre.microlight,
.swagger-ui .curl-command .curl{background:#060b1a!important;border:1px solid var(--border);
  border-radius:10px;font-family:'JetBrains Mono',monospace!important;font-size:12.5px;}
.swagger-ui .copy-to-clipboard{background:var(--panel);border-radius:8px;}

/* Models */
.swagger-ui section.models{background:var(--panel);border:1px solid var(--border);border-radius:14px;}
.swagger-ui section.models.is-open h4{border-bottom:1px solid var(--border);}
.swagger-ui .model-box,.swagger-ui .model-container{background:transparent;}
.swagger-ui .model-toggle:after{filter:invert(.8);}

/* Authorize dialog */
.swagger-ui .dialog-ux .modal-ux{background:var(--panel);border:1px solid var(--border);
  border-radius:16px;box-shadow:0 30px 80px rgba(0,0,0,.6);color:var(--text);}
.swagger-ui .dialog-ux .modal-ux-header{border-bottom:1px solid var(--border);}
.swagger-ui .dialog-ux .modal-ux-header .close-modal svg{fill:var(--muted);}
.swagger-ui .auth-container{border-bottom:1px solid var(--border);}
.swagger-ui .auth-btn-wrapper .btn-done{color:var(--muted);}

/* Misc */
.swagger-ui .loading-container .loading:after{color:var(--muted);}
.swagger-ui .errors-wrapper{background:rgba(248,113,113,.1);border:1px solid var(--delete);border-radius:10px;}
.swagger-ui .errors-wrapper .errors h4,.swagger-ui .errors-wrapper hgroup h4{color:var(--delete)!important;}
::selection{background:var(--accent);color:#fff;}
::-webkit-scrollbar{width:10px;height:10px;}
::-webkit-scrollbar-thumb{background:#2a3658;border-radius:8px;}
"""

SWAGGER_PARAMS = {
    "persistAuthorization": True,      # keep the login token after page refresh
    "displayRequestDuration": True,
    "docExpansion": "none",            # start collapsed
    "filter": True,                    # search box
    "tryItOutEnabled": True,
    "defaultModelsExpandDepth": -1,    # hide the Schemas section
    "syntaxHighlight.theme": "monokai",
}
