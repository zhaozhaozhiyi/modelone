window.MODELONE_BRAND = {"name": "AI\u5f00\u53d1\u8fd0\u8425\u5e73\u53f0", "internalName": "modelone", "title": "AI\u5f00\u53d1\u8fd0\u8425\u5e73\u53f0", "description": "AI \u5f00\u53d1\u4e0e\u6a21\u578b\u751f\u4ea7\u5e73\u53f0", "supportUrl": "https://modelone.local/support", "helpUrl": "https://modelone.local/help", "termsUrl": "https://modelone.local/terms", "privacyUrl": "https://modelone.local/privacy", "logoUrl": "/static/assets/modelone/modelone-logo.svg?v=20261010-ai-platform", "logoReverseUrl": "/static/assets/modelone/modelone-logo-reverse.svg?v=20261010-ai-platform", "faviconUrl": "/static/assets/modelone/modelone-mark.svg?v=20261010-ai-platform", "primaryColor": "#17191d", "secondaryColor": "#3b82f6", "loginBackgroundColor": "#f4f6f8", "loginSurfaceColor": "#ffffff", "fontFamily": "Inter, \"PingFang SC\", \"Microsoft YaHei\", sans-serif", "assetBaseUrl": "https://assets.modelone.local/modelone"};
window.applyModeloneBrand = function () {
  var b = window.MODELONE_BRAND;
  document.title = b.title;
  var icon = document.querySelector('link[rel="icon"]');
  if (icon && b.faviconUrl) icon.href = b.faviconUrl;
  var touchIcon = document.querySelector('link[rel="apple-touch-icon"]');
  if (touchIcon && b.faviconUrl) touchIcon.href = b.faviconUrl;
  var description = document.querySelector('meta[name="description"]');
  if (description) description.content = b.description;
  var themeColor = document.querySelector('meta[name="theme-color"]');
  if (themeColor && b.primaryColor) themeColor.content = b.primaryColor;
  document.documentElement.style.setProperty('--mo-brand-primary', b.primaryColor);
  document.documentElement.style.setProperty('--mo-brand-secondary', b.secondaryColor);
  document.documentElement.style.setProperty('--mo-login-background', b.loginBackgroundColor);
  document.documentElement.style.setProperty('--mo-login-surface', b.loginSurfaceColor);
  document.documentElement.style.setProperty('--mo-font-sans', b.fontFamily);
};
window.applyModeloneBrand();
