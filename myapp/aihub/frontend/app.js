const API = '/aihub/api';
const DEFAULT_INPUT = {type:'object',properties:{text:{type:'string',title:'文本',minLength:1}},required:['text'],additionalProperties:false};
const DEFAULT_OUTPUT = {type:'object',additionalProperties:true};
const CATEGORIES = ['机器视觉','语音','自然语言','多模态','大模型','其他'];
const state = {session:null,items:[],selected:null,detail:null,tab:'overview',page:1,total:0,search:'',category:'',adminItems:[],editing:null,health:{}};
const $ = id => document.getElementById(id);

function node(tag, className, content) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (content !== undefined) element.textContent = content;
  return element;
}

function button(label, className, action) {
  const element = node('button', className, label);
  element.type = 'button';
  element.addEventListener('click', action);
  return element;
}

let noticeTimer;
function notify(message) {
  const element = $('notice');
  element.textContent = message;
  element.classList.add('show');
  clearTimeout(noticeTimer);
  noticeTimer = setTimeout(() => element.classList.remove('show'), 5000);
}

async function api(path, options = {}, timeout = 15000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch(API + path, {
      credentials: 'same-origin',
      ...options,
      headers: {'Accept':'application/json', ...(options.body ? {'Content-Type':'application/json'} : {}),
        ...(state.session?.csrf_token ? {'X-CSRFToken':state.session.csrf_token} : {}), ...options.headers},
      signal: controller.signal
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error?.message || '请求失败，请重试');
    return payload.data;
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('请求超时，请重试');
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

function setView(name) {
  $('catalog-view').hidden = name !== 'catalog';
  $('admin-view').hidden = name !== 'admin';
  $('nav-catalog').classList.toggle('active', name === 'catalog');
  $('nav-admin').classList.toggle('active', name === 'admin');
  $('page-title').textContent = name === 'catalog' ? '应用目录' : '应用管理';
  $('page-context').textContent = name === 'catalog' ? '已发布的模型应用' : '接入与发布';
  if (name === 'admin') loadAdmin();
  else loadCatalog();
}

function loading(container, message = '正在加载…') {
  container.replaceChildren(node('div', 'empty-state', message));
}

function empty(container, title, message, actionLabel, action) {
  const wrapper = node('div', 'empty-state');
  wrapper.append(node('h2', '', title), node('p', '', message));
  if (actionLabel) wrapper.append(button(actionLabel, '', action));
  container.replaceChildren(wrapper);
}

async function loadCatalog() {
  const container = $('catalog-list');
  loading(container);
  const params = new URLSearchParams({page:String(state.page)});
  const requestKey = `${state.page}|${state.search}|${state.category}`;
  if (state.search) params.set('q', state.search);
  if (state.category) params.set('category', state.category);
  try {
    const data = await api('/apps?' + params);
    if (requestKey !== `${state.page}|${state.search}|${state.category}`) return;
    state.items = data.items;
    state.total = data.total;
    $('catalog-count').textContent = `${data.total} 个应用`;
    const filter = $('category');
    if (filter.options.length === 1) {
      data.categories.forEach(category => filter.add(new Option(category, category)));
      filter.value = state.category;
    }
    renderCatalog();
  } catch (error) {
    $('catalog-count').textContent = '加载失败';
    empty(container, '应用目录暂不可用', error.message, '重试', loadCatalog);
    $('pagination').hidden = true;
  }
}

function renderCatalog() {
  const container = $('catalog-list');
  container.replaceChildren();
  if (!state.items.length) {
    const title = state.search || state.category ? '没有匹配的应用' : '还没有已发布的应用';
    const message = state.search || state.category ? '试试其他搜索词或分类。' : '管理员可以登记运行端点并发布第一个应用。';
    empty(container, title, message, state.session.is_admin && !state.search && !state.category ? '登记应用' : '', () => {
      setView('admin'); openEditor();
    });
  } else {
    state.items.forEach(app => {
      const row = button('', 'app-row', () => selectApp(app.slug, app.version));
      row.setAttribute('aria-label', `查看 ${app.name}，版本 ${app.version}`);
      row.dataset.slug = app.slug;
      if (state.selected?.slug === app.slug) row.classList.add('selected');
      const glyph = node('span', 'app-glyph', app.category.slice(0, 1));
      glyph.setAttribute('aria-hidden', 'true');
      const copy = node('span', 'app-row-copy');
      const heading = node('span', 'app-row-heading');
      heading.append(node('strong', '', app.name), node('span', 'version-small', app.version));
      copy.append(heading, node('span', 'app-row-meta', [app.category, app.task].filter(Boolean).join(' · ')),
                  node('span', 'app-row-summary', app.summary || '暂无简介'));
      row.append(glyph, copy);
      container.append(row);
    });
  }
  const pages = Math.ceil(state.total / 24);
  $('pagination').hidden = pages <= 1;
  $('page-indicator').textContent = `${state.page} / ${pages}`;
  $('prev-page').disabled = state.page <= 1;
  $('next-page').disabled = state.page >= pages;
  if (state.items.length && !state.items.some(item => item.slug === state.selected?.slug && item.version === state.selected?.version)) {
    selectApp(state.items[0].slug, state.items[0].version);
  } else if (state.items.length && state.selected) {
    document.querySelectorAll('.app-row').forEach(row => row.classList.toggle('selected', row.dataset.slug === state.selected.slug));
  } else if (!state.items.length) {
    state.selected = null;
    $('detail-pane').replaceChildren(node('div', 'detail-placeholder', '暂无可查看的应用'));
  }
}

async function selectApp(slug, version) {
  state.selected = {slug, version};
  document.querySelectorAll('.app-row').forEach(row => row.classList.toggle('selected', row.dataset.slug === slug));
  loading($('detail-pane'), '正在加载应用详情…');
  try {
    const [detail, selectedVersion] = await Promise.all([api('/apps/' + encodeURIComponent(slug)),
      api('/apps/' + encodeURIComponent(slug) + '/versions/' + encodeURIComponent(version))]);
    if (state.selected?.slug !== slug || state.selected?.version !== version) return;
    state.detail = detail;
    renderDetail(selectedVersion, detail.versions);
    loadHealth(slug, version);
    if (window.matchMedia('(max-width: 700px)').matches) $('detail-pane').scrollIntoView({behavior:'smooth',block:'start'});
  } catch (error) {
    empty($('detail-pane'), '详情加载失败', error.message, '重试', () => selectApp(slug, version));
  }
}

function fieldList(schema) {
  const list = node('ul', 'field-list');
  Object.entries(schema.properties || {}).forEach(([key, spec]) => {
    const item = node('li');
    const name = node('strong', '', spec.title || key);
    if ((schema.required || []).includes(key)) name.append(node('em', '', ' 必填'));
    item.append(name, node('span', '', `${key} · ${spec.type || 'any'}`));
    list.append(item);
  });
  return list;
}

function renderDetail(app, versions) {
  const pane = $('detail-pane');
  pane.replaceChildren();
  const header = node('div', 'detail-header');
  const intro = node('div');
  intro.append(node('span', 'overline', `${app.category} / ${app.task || '模型应用'}`),
               node('h2', '', app.name), node('p', '', app.summary || '暂无简介'));
  const meta = node('div', 'detail-meta');
  meta.append(node('span', '', `应用 ID: ${app.slug}`), node('span', '', '·'),
              node('span', '', app.visibility === 'public' ? '平台可见' : app.visibility === 'project' ? '项目可见' : '仅创建者'));
  const health = state.health[`${app.slug}@${app.version}`];
  const status = node('span', 'status ' + (health?.status || 'checking'),
    health ? health.status === 'healthy' ? '端点可用' : '端点不可用' : '检查端点中');
  if (health?.reason) status.title = health.reason;
  status.id = 'endpoint-status';
  meta.append(node('span', '', '·'), status);
  intro.append(meta);
  const versionLabel = node('label', 'detail-version', '版本');
  const versionSelect = node('select');
  versions.forEach(item => versionSelect.add(new Option(item.version, item.version)));
  versionSelect.value = app.version;
  versionSelect.addEventListener('change', () => selectApp(app.slug, versionSelect.value));
  versionLabel.append(versionSelect);
  header.append(intro, versionLabel);
  const tabs = node('div', 'detail-tabs');
  [['overview','概览'],['playground','在线体验'],['api','API']].forEach(([key,label]) => {
    const tab = button(label, 'detail-tab' + (state.tab === key ? ' active' : ''), () => {
      state.tab = key;
      renderDetail(app, versions);
    });
    tab.setAttribute('role', 'tab');
    tab.setAttribute('aria-selected', state.tab === key ? 'true' : 'false');
    tabs.append(tab);
  });
  tabs.setAttribute('role', 'tablist');
  const body = node('div', 'detail-body');
  if (state.tab === 'overview') renderOverview(body, app);
  else if (state.tab === 'playground') renderPlayground(body, app);
  else renderApi(body, app);
  pane.append(header, tabs, body);
}

function renderOverview(body, app) {
  const section = node('section', 'detail-section');
  section.append(node('h3', '', '应用信息'));
  const definition = node('dl', 'definition');
  [['版本',app.version],['任务',app.task || '未填写'],['分类',app.category],
    ['许可',app.license_name],['权重摘要',app.weight_digest || '未提供'],
    ['发布时间',app.published_at ? new Date(app.published_at).toLocaleString('zh-CN') : '未发布']].forEach(([label,value]) => {
    definition.append(node('dt', '', label), node('dd', '', value));
  });
  section.append(definition);
  const source = node('section','detail-section');
  source.append(node('h3','','模型来源'));
  const sourceLink = node('a','',app.model_source);
  sourceLink.href = app.model_source;
  sourceLink.target = '_blank';
  sourceLink.rel = 'noopener noreferrer';
  source.append(sourceLink);
  const input = node('section', 'detail-section');
  input.append(node('h3', '', '输入字段'), fieldList(app.input_schema));
  const output = node('section', 'detail-section');
  output.append(node('h3', '', '输出 Schema'), node('pre', 'code-box', JSON.stringify(app.output_schema, null, 2)));
  body.append(section, source, input, output);
}

function renderPlayground(body, app) {
  const form = node('form', 'playground');
  form.noValidate = true;
  const fields = {};
  Object.entries(app.input_schema.properties || {}).forEach(([key,spec]) => {
    const label = node('label', '', spec.title || key);
    const control = spec.type === 'boolean' ? node('select') : spec.type === 'string' && (spec.format === 'textarea' || (spec.maxLength || 0) > 300) ? node('textarea') : node('input');
    if (spec.type === 'boolean') {control.add(new Option('否','false'));control.add(new Option('是','true'));}
    else if (spec.type === 'number' || spec.type === 'integer') {control.type = 'number';control.step = spec.type === 'integer' ? '1' : 'any';}
    else if (control.tagName === 'INPUT') control.type = 'text';
    if ((app.input_schema.required || []).includes(key)) control.required = true;
    if (spec.description) control.placeholder = spec.description;
    fields[key] = {control,spec};
    label.append(control);form.append(label);
  });
  const actions = node('div', 'playground-actions');
  const run = node('button', 'button primary', '运行体验');
  run.type = 'submit';
  actions.append(run);
  const error = node('p', 'inline-error');
  error.setAttribute('role','alert');
  const result = node('pre', 'result-box');
  result.hidden = true;
  form.append(actions,error,result);
  form.addEventListener('submit', async event => {
    event.preventDefault();
    error.textContent = '';
    if (!form.reportValidity()) return;
    const inputs = {};
    Object.entries(fields).forEach(([key,{control,spec}]) => {
      if (spec.type === 'boolean') inputs[key] = control.value === 'true';
      else if (spec.type === 'number' || spec.type === 'integer') {if (control.value !== '') inputs[key] = Number(control.value);}
      else if (control.value !== '' || (app.input_schema.required || []).includes(key)) inputs[key] = control.value;
    });
    run.disabled = true;run.textContent = '运行中…';result.hidden = true;
    try {
      const data = await api(`/apps/${encodeURIComponent(app.slug)}/versions/${encodeURIComponent(app.version)}/predict`,
        {method:'POST',body:JSON.stringify({inputs})},45000);
      result.textContent = JSON.stringify(data.result,null,2);
      result.hidden = false;
    } catch (failure) {error.textContent = failure.message;}
    finally {run.disabled = false;run.textContent = '运行体验';}
  });
  body.append(form);
}

function renderApi(body, app) {
  const path = `/aihub/api/apps/${encodeURIComponent(app.slug)}/versions/${encodeURIComponent(app.version)}/predict`;
  const section = node('section', 'detail-section');
  section.append(node('h3', '', '调用地址'),node('div', 'api-path', `POST ${path}`));
  const sample = {};
  Object.entries(app.input_schema.properties || {}).forEach(([key,spec]) => {
    sample[key] = spec.type === 'boolean' ? false : spec.type === 'number' || spec.type === 'integer' ? 0 : spec.example || '';
  });
  const example = node('section', 'detail-section');
  example.append(node('h3', '', '请求示例'),node('pre', 'code-box',
    `curl -X POST '${location.origin}${path}' \\\n+  -H 'Authorization: Bearer <平台 API 令牌>' \\\n+  -H 'Content-Type: application/json' \\\n+  -d '${JSON.stringify({inputs:sample})}'`));
  const contract = node('section', 'detail-section');
  contract.append(node('h3', '', '响应约定'),node('pre', 'code-box', JSON.stringify({data:{result:'...',version:app.version}},null,2)));
  body.append(section,example,contract);
}

async function loadHealth(slug, version) {
  try {
    const data = await api(`/apps/${encodeURIComponent(slug)}/versions/${encodeURIComponent(version)}/health`,{},12000);
    state.health[`${slug}@${version}`] = data;
    if (state.selected?.slug !== slug || state.selected?.version !== version) return;
    const status = $('endpoint-status');
    if (!status) return;
    status.className = 'status ' + data.status;
    status.textContent = data.status === 'healthy' ? '端点可用' : '端点不可用';
    if (data.reason) status.title = data.reason;
  } catch (_) {
    const status = $('endpoint-status');
    if (status) {status.className = 'status unavailable';status.textContent = '状态未知';}
  }
}

async function loadAdmin() {
  const container = $('admin-list');
  loading(container);
  try {
    const data = await api('/admin/apps');
    state.adminItems = data.items;
    renderAdmin();
  } catch (error) {empty(container,'管理列表加载失败',error.message,'重试',loadAdmin);}
}

function renderAdmin() {
  const container = $('admin-list');
  container.replaceChildren();
  if (!state.adminItems.length) {
    empty(container,'还没有接入应用','登记一个已有运行端点的应用，校验后发布。','登记应用',openEditor);
    return;
  }
  state.adminItems.forEach(app => {
    const row = node('div','admin-row');
    const copy = node('div');
    copy.append(node('div','admin-row-title',`${app.name} · ${app.version}`));
    const meta = node('div','admin-row-meta');
    meta.append(node('span','',`${app.slug} · ${app.category} · `),
      node('span','admin-state ' + app.state,app.state === 'draft' ? '草稿' : app.state === 'published' ? '已发布' : '已下架'));
    copy.append(meta);
    const actions = node('div','admin-row-actions');
    if (app.state === 'draft') {
      actions.append(button('编辑','button',() => openEditor(app)));
      actions.append(button('校验并发布','button primary',() => changeState(app,'publish')));
    }
    if (app.state === 'published') actions.append(button('下架','button danger',() => changeState(app,'retire')));
    row.append(copy,actions);container.append(row);
  });
}

async function changeState(app, action) {
  const verb = action === 'publish' ? '发布' : '下架';
  if (!window.confirm(`确认${verb} ${app.name} ${app.version}？`)) return;
  try {
    await api(`/admin/apps/${app.id}/${action}`,{method:'POST'});
    notify(`${verb}成功`);
    await loadAdmin();
    await loadCatalog();
  } catch (error) {notify(`${verb}失败：${error.message}`);}
}

function openEditor(app = null) {
  state.editing = app;
  const form = $('app-form');
  form.reset();
  $('form-error').hidden = true;
  $('editor-title').textContent = app ? '编辑草稿' : '登记应用';
  const values = app || {slug:'',version:'',name:'',summary:'',category:'自然语言',task:'',model_source:'',license_name:'',weight_digest:'',visibility:'public',project_id:'',
    endpoint_url:'',endpoint_revision:'',credential_env:'',input_schema:DEFAULT_INPUT,output_schema:DEFAULT_OUTPUT};
  Object.keys(values).forEach(key => {
    if (form.elements[key]) form.elements[key].value = key.endsWith('_schema') ? JSON.stringify(values[key],null,2) : values[key] ?? '';
  });
  $('project-row').hidden = form.elements.visibility.value !== 'project';
  $('editor').showModal();
  form.elements.slug.focus();
}

function closeEditor() {$('editor').close();state.editing = null;}

async function saveEditor(event) {
  event.preventDefault();
  const form = $('app-form');
  if (!form.reportValidity()) return;
  const data = Object.fromEntries(new FormData(form));
  const error = $('form-error');
  try {
    data.input_schema = JSON.parse(data.input_schema);
    data.output_schema = JSON.parse(data.output_schema);
    data.project_id = data.visibility === 'project' ? Number(data.project_id) : null;
    if (data.visibility === 'project' && (!Number.isInteger(data.project_id) || data.project_id < 1)) throw new Error('请填写有效的项目空间 ID');
    $('save-app').disabled = true;$('save-app').textContent = '保存中…';
    await api(state.editing ? `/admin/apps/${state.editing.id}` : '/admin/apps',
      {method:state.editing ? 'PUT' : 'POST',body:JSON.stringify(data)});
    closeEditor();notify('草稿已保存');await loadAdmin();
  } catch (failure) {error.textContent = failure instanceof SyntaxError ? 'JSON Schema 格式无效' : failure.message;error.hidden = false;error.scrollIntoView({block:'nearest'});}
  finally {$('save-app').disabled = false;$('save-app').textContent = '保存草稿';}
}

function bindEvents() {
  CATEGORIES.forEach(category => $('app-form').elements.category.add(new Option(category, category)));
  $('nav-catalog').addEventListener('click',() => setView('catalog'));
  $('nav-admin').addEventListener('click',() => setView('admin'));
  $('search').addEventListener('input',() => {
    clearTimeout(bindEvents.searchTimer);
    bindEvents.searchTimer = setTimeout(() => {state.search = $('search').value.trim();state.page = 1;loadCatalog();},250);
  });
  $('category').addEventListener('change',() => {state.category = $('category').value;state.page = 1;loadCatalog();});
  $('prev-page').addEventListener('click',() => {state.page -= 1;loadCatalog();});
  $('next-page').addEventListener('click',() => {state.page += 1;loadCatalog();});
  $('new-app').addEventListener('click',() => openEditor());
  $('close-editor').addEventListener('click',closeEditor);
  $('cancel-editor').addEventListener('click',closeEditor);
  $('app-form').addEventListener('submit',saveEditor);
  $('app-form').elements.visibility.addEventListener('change',event => {$('project-row').hidden = event.target.value !== 'project';});
}

async function start() {
  bindEvents();
  loading($('catalog-list'));
  try {
    state.session = await api('/session');
    $('username').textContent = state.session.username;
    $('nav-admin').hidden = !state.session.is_admin;
    await loadCatalog();
  } catch (error) {
    empty($('catalog-list'),'无法进入 AIHub',error.message,'重试',start);
  }
}

start();
