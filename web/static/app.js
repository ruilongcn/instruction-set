/* 指令集研发智能体团队 - 前端交互 */
"use strict";

/* ---------- Tab 切换 ---------- */
document.querySelectorAll('.tab').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('view-' + btn.dataset.view).classList.add('active');
  });
});

/* ---------- 工具函数 ---------- */
async function api(path, body) {
  const opt = { headers: { 'Content-Type': 'application/json' } };
  if (body !== undefined) opt.method = 'POST', opt.body = JSON.stringify(body);
  const resp = await fetch(path, opt);
  if (!resp.ok) throw new Error('HTTP ' + resp.status);
  return resp.json();
}
function show(el, data) {
  el.classList.remove('hidden');
  el.textContent = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
}
function lines(val) { return val.split('\n').map(s => s.trim()).filter(Boolean); }

/* ---------- ISA 设计 ---------- */
async function isaDesign() {
  const el = document.getElementById('isaResult');
  try {
    const r = await api('/api/tasks', {
      goal: '设计自主指令集架构',
      params: {
        action: 'design_spec',
        isa_name: document.getElementById('isaName').value,
        xlen: parseInt(document.getElementById('isaXlen').value),
        base_isa: document.getElementById('isaBase').value,
        extensions: lines(document.getElementById('isaExt').value)
      }
    });
    show(el, r.results[0].result.spec);
  } catch (e) { show(el, '错误: ' + e.message); }
}
async function extDefine() {
  const el = document.getElementById('extResult');
  try {
    const r = await api('/api/tasks', {
      goal: '定义自主扩展指令',
      params: { action: 'define_extension',
        extension_name: document.getElementById('extName').value,
        description: document.getElementById('extDesc').value }
    });
    show(el, r.results[0].result.extension);
  } catch (e) { show(el, '错误: ' + e.message); }
}

/* ---------- 编码/解码 ---------- */
async function encRun() {
  const el = document.getElementById('encResult');
  try {
    const r = await api('/api/tasks', {
      goal: '指令编码',
      params: { action: 'encode', instructions: lines(document.getElementById('encInput').value).map(a => ({ asm: a })) }
    });
    show(el, r.results[0].result.items);
  } catch (e) { show(el, '错误: ' + e.message); }
}
async function decRun() {
  const el = document.getElementById('decResult');
  try {
    const r = await api('/api/tasks', {
      goal: '指令解码',
      params: { action: 'decode', hex_list: document.getElementById('decInput').value.split(',').map(s => s.trim()) }
    });
    show(el, r.results[0].result.items);
  } catch (e) { show(el, '错误: ' + e.message); }
}

/* ---------- 汇编/反汇编 ---------- */
async function asmRun() {
  const el = document.getElementById('asmResult');
  try {
    const r = await api('/api/tasks', {
      goal: '汇编',
      params: { action: 'assemble', source: lines(document.getElementById('asmInput').value) }
    });
    show(el, r.results[0].result.items);
  } catch (e) { show(el, '错误: ' + e.message); }
}
async function disasmRun() {
  const el = document.getElementById('disasmResult');
  try {
    const r = await api('/api/tasks', {
      goal: '反汇编',
      params: { action: 'disassemble', hex_list: document.getElementById('disasmInput').value.split(',').map(s => s.trim()) }
    });
    show(el, r.results[0].result.items);
  } catch (e) { show(el, '错误: ' + e.message); }
}

/* ---------- 微架构映射 ---------- */
async function maRun() {
  const el = document.getElementById('maResult');
  try {
    const r = await api('/api/tasks', {
      goal: '微架构映射',
      params: { action: 'map', super_scalar: document.getElementById('maSuper').checked }
    });
    show(el, r.results[0].result);
  } catch (e) { show(el, '错误: ' + e.message); }
}

/* ---------- RISC-V 生态 ---------- */
async function ecoSweep() {
  const el = document.getElementById('ecoResult');
  try {
    const r = await api('/api/tasks', { goal: 'RISC-V 开放生态调研', params: { action: 'survey' } });
    show(el, r.results[0].result);
  } catch (e) { show(el, '错误: ' + e.message); }
}
async function ecoCompat() {
  const el = document.getElementById('ecoCompatResult');
  try {
    const r = await api('/api/tasks', {
      goal: '自主 ISA 与 RISC-V 兼容策略',
      params: { action: 'compatibility', target_isa: document.getElementById('ecoCompatIsa').value }
    });
    show(el, r.results[0].result);
  } catch (e) { show(el, '错误: ' + e.message); }
}

/* ---------- 兼容与基准 ---------- */
async function benchPlan() {
  const el = document.getElementById('benchPlanResult');
  try {
    const r = await api('/api/tasks', { goal: '合规测试规划', params: { action: 'plan' } });
    show(el, r.results[0].result);
  } catch (e) { show(el, '错误: ' + e.message); }
}
async function benchRun() {
  const el = document.getElementById('benchResult');
  try {
    const r = await api('/api/tasks', {
      goal: '基准测试',
      params: { action: 'benchmark', cases: lines(document.getElementById('benchCases').value) }
    });
    show(el, r.results[0].result);
  } catch (e) { show(el, '错误: ' + e.message); }
}

/* ---------- 流水线编排 ---------- */
async function plRun() {
  const el = document.getElementById('plResult');
  try {
    const r = await api('/api/tasks', { goal: document.getElementById('plGoal').value, params: {} });
    show(el, r);
  } catch (e) { show(el, '错误: ' + e.message); }
}

/* ---------- 系统健康 ---------- */
async function loadSystem() {
  try {
    const h = await api('/api/health');
    document.getElementById('sysHealth').textContent = JSON.stringify(h, null, 2);
    const a = await api('/api/agents');
    document.getElementById('sysAgents').textContent = JSON.stringify(a, null, 2);
    const cards = document.getElementById('sysCards');
    const list = a.agents.map(x => `<div class="card"><b>${x.name}</b><div class="hint">${x.description}</div></div>`).join('');
    cards.innerHTML = list;
  } catch (e) {
    document.getElementById('sysHealth').textContent = '错误: ' + e.message;
  }
}
loadSystem();
