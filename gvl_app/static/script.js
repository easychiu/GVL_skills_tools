// GVL 裝備表前端 JavaScript

// 全局狀態
let state = {
    currentPage: 1,
    perPage: 20,
    totalPages: 1,
    characterOptions: null,
    equipmentSkillsMap: {},
    allSkills: [],
    autoBuildPlans: []
};

const CHARACTER_SLOT_SIDE_ORDER = [
    ['飾品1', 'left'],
    ['飾品2', 'left'],
    ['寶物1', 'left'],
    ['寶物2', 'left'],
    ['主武', 'left'],
    ['副武', 'left'],
    ['頭盔', 'right'],
    ['衣服', 'right'],
    ['手套', 'right'],
    ['鞋子', 'right']
];
const CHARACTER_SLOT_SIDE_MAP = Object.fromEntries(CHARACTER_SLOT_SIDE_ORDER);
const CHARACTER_DUPLICATE_POSITIONS = new Set(['飾品', '寶物']);
const DEFAULT_SLOT_SIDE = 'right';
const DUPLICATE_SLOT_COUNT = 2;

// 裝備類型判斷：砲術系 vs 白兵(跳幫)系
// 名稱必須與資料源的技能欄位完全一致（是「炮術」不是「砲術」、「水平射擊」不是「水平」）
const CANNON_SKILLS = new Set(['炮術', '水平射擊', '彈道學', '貫穿', '速射']);
const BOARDING_SKILLS = new Set(['突擊', '戰術', '射擊']);

// 一鍵套用的優先技能組合。只有 5 個優先技能欄位，所以每組最多 5 個技能
const SKILL_PRESETS = [
    ['砲術裝備', ['炮術', '水平射擊', '彈道學', '貫穿', '速射']],
    ['冒險陸戰', ['迅捷', '識破', '猛擊']],
    ['海事白兵', ['劍術', '突擊', '戰術', '射擊', '防禦']]
];

// 下拉選單的 optgroup 分組。範圍比一鍵組合大——分組不受 5 個欄位的限制，
// 例如齊射屬砲術類但一鍵組合已滿。未列入的技能會歸到「其他」。
// 純顯示用，不影響任何計算。
const SKILL_GROUPS = [
    ['砲術類', ['炮術', '水平射擊', '彈道學', '貫穿', '速射', '齊射']],
    ['冒險類', ['迅捷', '識破', '猛擊', '搜尋']],
    ['白兵類', ['劍術', '突擊', '戰術', '射擊', '防禦']]
];

/**
 * 依技能判斷裝備類型：cannon（砲術系）、boarding（白兵系）或 neutral
 * @param {string} name 裝備名稱
 * @returns {'cannon'|'boarding'|'neutral'}
 */
function classifyEquipment(name) {
    const skills = state.equipmentSkillsMap[name] || {};
    let cannonScore = 0;
    let boardingScore = 0;
    for (const [skill, level] of Object.entries(skills)) {
        if (CANNON_SKILLS.has(skill)) cannonScore += level;
        if (BOARDING_SKILLS.has(skill)) boardingScore += level;
    }
    // 砲術系分數 >= 白兵系分數時（含平手）優先歸類為砲術系
    if (cannonScore > 0 && cannonScore >= boardingScore) return 'cannon';
    if (boardingScore > 0 && boardingScore > cannonScore) return 'boarding';
    return 'neutral';
}

/**
 * 依裝備類型更新選單底色
 * @param {HTMLSelectElement} selectEl
 */
function updateSlotColor(selectEl) {
    const type = selectEl.value ? classifyEquipment(selectEl.value) : 'neutral';
    selectEl.classList.remove('slot-cannon', 'slot-boarding');
    if (type === 'cannon') {
        selectEl.classList.add('slot-cannon');
    } else if (type === 'boarding') {
        selectEl.classList.add('slot-boarding');
    }
}

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// ── 版本與更新日誌 ────────────────────────────────────────────────────────
// 每次上線改動請在 CHANGELOG 最前面新增一筆，並把 APP_VERSION 更新為當天日期。
// DATA_VERSION 是裝備資料對應的遊戲改版，資料同步後才需要改。
const APP_VERSION = 'v2026.08.20';
const DATA_VERSION = '資料：2026-07-06 印度改版';

const CHANGELOG = [
    {
        date: '2026-08-20',
        version: 'v2026.08.20',
        items: [
            '網頁版上線：免安裝、手機可直接用',
            '自動配裝改用可證明最佳解的搜尋，同時提供「順序最高」與「綜合最高」兩種方案',
            '自動配裝以遊戲內最高值（角色上限＋裝備＋航海士）為目標，不再把技能堆過 25 浪費',
            '新增一鍵套用：砲術裝備／冒險陸戰／海事白兵',
            '優先技能下拉改為砲術類／冒險類／白兵類分組',
            '手機版排版大改：可用寬度增加三成、配裝結果改卡片式、觸控目標放大',
            '裝備分頁新增依部位篩選',
            '角色配裝改為開啟時的預設頁',
            '溫庫隆庫魯雕像、托特的護符標記為唯一裝備（質變版與原版視為同一件）',
            '修正各職業技能上限未正確載入——先前所有職業都誤用大提督／打撈者的上限',
            '修正砲術系配色的技能名稱與資料不符（炮術／水平射擊／彈道學）',
            '修正三件質變裝備在 Excel 下拉選單中選不到'
        ]
    },
    {
        date: '2026-07-31',
        version: '',
        items: ['同步巴哈姆特整理帖裝備資料至 2026-07-06 印度改版']
    },
    {
        date: '2026-04-24',
        version: '',
        items: ['新增質變裝備資料', '技能分解總覽移至頁面下方']
    }
];

/**
 * 渲染標題列的版本標籤與更新日誌分頁
 */
function renderVersionAndChangelog() {
    const appEl = document.getElementById('appVersion');
    const dataEl = document.getElementById('dataVersion');
    if (appEl) appEl.textContent = APP_VERSION;
    if (dataEl) dataEl.textContent = DATA_VERSION;

    const list = document.getElementById('changelogList');
    if (!list) return;
    list.innerHTML = CHANGELOG.map(entry => `
        <div class="changelog-entry">
            <div class="changelog-date">
                ${escapeHtml(entry.date)}
                ${entry.version ? `<span class="changelog-version">${escapeHtml(entry.version)}</span>` : ''}
            </div>
            <ul class="changelog-items">
                ${entry.items.map(t => `<li>${escapeHtml(t)}</li>`).join('')}
            </ul>
        </div>
    `).join('');
}

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initializePage();
});

// 初始化頁面
function initializePage() {
    loadPositions();
    loadSkills();
    loadEquipmentPage();
    loadCharacterOptions();
    loadStats();
    setupTabHandlers();
    setupAutoBuilderListeners();
    setupEquipmentFilter();
    renderVersionAndChangelog();
}

// 設置裝備頁的位置篩選
function setupEquipmentFilter() {
    const filter = document.getElementById('equipmentPositionFilter');
    if (!filter) return;
    filter.addEventListener('change', function () {
        state.currentPage = 1;
        loadEquipmentPage();
    });
}

// 設置標籤處理器
function setupTabHandlers() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const tabName = this.dataset.tab;
            switchTab(tabName);
        });
    });
}

// 切換標籤
function switchTab(tabName) {
    // 隱藏所有標籤內容
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // 移除所有按鈕的活躍狀態
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // 顯示選中的標籤
    document.getElementById(tabName).classList.add('active');
    
    // 標記按鈕為活躍
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
}

// 加載位置列表
function loadPositions() {
    fetch('/api/positions')
        .then(response => response.json())
        .then(data => {
            // 搜索頁的位置下拉，以及裝備頁的位置篩選，兩者選項相同
            ['positionSelect', 'equipmentPositionFilter'].forEach(id => {
                const select = document.getElementById(id);
                if (!select) return;
                data.positions.forEach(position => {
                    const option = document.createElement('option');
                    option.value = position;
                    option.textContent = position;
                    select.appendChild(option);
                });
            });
        })
        .catch(error => console.error('Error loading positions:', error));
}

// 加載技能列表
function loadSkills() {
    fetch('/api/skills')
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('skillSelect');
            data.skills.forEach(skill => {
                const option = document.createElement('option');
                option.value = skill;
                option.textContent = skill;
                select.appendChild(option);
            });
            state.allSkills = data.skills;
            renderAutoBuildSkillDropdowns(data.skills);
        })
        .catch(error => console.error('Error loading skills:', error));
}

// 按名稱搜索
function searchByName() {
    const keyword = document.getElementById('searchName').value.trim();
    if (!keyword) {
        alert('請輸入搜索關鍵字');
        return;
    }
    
    fetch(`/api/search?q=${encodeURIComponent(keyword)}&type=name`)
        .then(response => response.json())
        .then(data => {
            displaySearchResults(data);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('搜索失敗');
        });
}

// 按技能搜索
function searchBySkill() {
    const skill = document.getElementById('skillSelect').value;
    const minLevel = parseInt(document.getElementById('minLevel').value) || 1;
    
    if (!skill) {
        alert('請選擇技能');
        return;
    }
    
    fetch(`/api/search?q=${encodeURIComponent(skill)}&type=skill&min_level=${minLevel}`)
        .then(response => response.json())
        .then(data => {
            displaySearchResults(data);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('搜索失敗');
        });
}

// 按位置搜索
function searchByPosition() {
    const position = document.getElementById('positionSelect').value;
    
    if (!position) {
        alert('請選擇位置');
        return;
    }
    
    fetch(`/api/search?q=${encodeURIComponent(position)}&type=position`)
        .then(response => response.json())
        .then(data => {
            displaySearchResults(data);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('搜索失敗');
        });
}

// 顯示搜索結果
function displaySearchResults(data) {
    const resultsDiv = document.getElementById('searchResults');
    const resultsList = document.getElementById('resultsList');
    
    if (data.results.length === 0) {
        resultsList.innerHTML = '<div class="error">未找到匹配的結果</div>';
    } else {
        resultsList.innerHTML = '';
        
        // 創建表格
        const table = document.createElement('table');
        table.className = 'equipment-table';
        
        const thead = document.createElement('thead');
        thead.innerHTML = `
            <tr>
                <th>位置</th>
                <th>裝備名稱</th>
                <th>技能加成</th>
            </tr>
        `;
        table.appendChild(thead);
        
        const tbody = document.createElement('tbody');
        data.results.forEach(eq => {
            const skillsStr = Object.entries(eq.skills)
                .map(([skill, level]) => `${skill}(+${level})`)
                .join(', ') || '無';
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${eq.position}</td>
                <td>${eq.name}</td>
                <td>${skillsStr}</td>
            `;
            tbody.appendChild(row);
        });
        table.appendChild(tbody);
        
        resultsList.appendChild(table);
    }
    
    resultsDiv.style.display = 'block';
    resultsDiv.scrollIntoView({ behavior: 'smooth' });
}

// 加載裝備頁面
function loadEquipmentPage() {
    const position = document.getElementById('equipmentPositionFilter')?.value || '';
    const pagination = document.getElementById('equipmentPagination');

    // 篩選特定位置時，該位置裝備最多不到百件，直接一次列出、不分頁
    if (position) {
        fetch(`/api/search?q=${encodeURIComponent(position)}&type=position`)
            .then(response => response.json())
            .then(data => {
                displayEquipmentGrid(data.results);
                document.getElementById('equipmentCount').textContent =
                    `${position}：共 ${data.count} 件裝備`;
                if (pagination) pagination.style.display = 'none';
            })
            .catch(error => console.error('Error loading equipment:', error));
        return;
    }

    if (pagination) pagination.style.display = '';
    fetch(`/api/equipment?page=${state.currentPage}&per_page=${state.perPage}`)
        .then(response => response.json())
        .then(data => {
            state.totalPages = data.pages;
            displayEquipmentGrid(data.equipment);
            updatePageInfo(data);
        })
        .catch(error => console.error('Error loading equipment:', error));
}

// 顯示裝備網格
function displayEquipmentGrid(equipment) {
    const grid = document.getElementById('equipmentList');
    grid.innerHTML = '';
    
    equipment.forEach(eq => {
        const card = document.createElement('div');
        card.className = 'equipment-card';
        
        const skillsHtml = Object.entries(eq.skills)
            .map(([skill, level]) => `<span class="skill-item">${skill}(+${level})</span>`)
            .join('');
        
        card.innerHTML = `
            <div class="equipment-card-position">${eq.position}</div>
            <div class="equipment-card-title">${eq.name}</div>
            <div class="equipment-card-skills">
                ${skillsHtml || '<em>無技能加成</em>'}
            </div>
        `;
        grid.appendChild(card);
    });
}

// 更新頁面信息
function updatePageInfo(data) {
    const pageInfo = document.getElementById('pageInfo');
    const equipmentCount = document.getElementById('equipmentCount');
    
    pageInfo.textContent = `第 ${data.page} / ${data.pages} 頁`;
    equipmentCount.textContent = `共 ${data.total} 件裝備`;
}

// 上一頁
function previousPage() {
    if (state.currentPage > 1) {
        state.currentPage--;
        loadEquipmentPage();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

// 下一頁
function nextPage() {
    if (state.currentPage < state.totalPages) {
        state.currentPage++;
        loadEquipmentPage();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

// 加載配置
function loadConfig(configName) {
    fetch(`/api/config/${configName}`)
        .then(response => response.json())
        .then(data => {
            displayConfig(data);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('加載配置失敗');
        });
}

// 顯示配置
function displayConfig(data) {
    const configContent = document.getElementById('configContent');
    configContent.innerHTML = `<h3>${data.name}</h3>`;
    
    Object.entries(data.config).forEach(([position, equipment]) => {
        if (equipment && equipment.length > 0) {
            const positionDiv = document.createElement('div');
            positionDiv.className = 'config-position';
            
            let html = `<div class="config-position-title">${position}</div>`;
            
            equipment.forEach(eq => {
                if (eq) {
                    const skillsStr = Object.entries(eq.skills)
                        .map(([skill, level]) => `${skill}(+${level})`)
                        .join(', ') || '無技能加成';
                    
                    html += `
                        <div class="config-item">
                            <span class="config-item-name">${eq.name}</span>
                            <span class="config-item-skills">${skillsStr}</span>
                        </div>
                    `;
                }
            });
            
            positionDiv.innerHTML = html;
            configContent.appendChild(positionDiv);
        }
    });
    
    configContent.style.display = 'block';
}

// 加載統計信息
function loadStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            displayStats(data);
        })
        .catch(error => console.error('Error loading stats:', error));
}

// 加載角色配裝選項
function loadCharacterOptions() {
    fetch('/api/character/options')
        .then(response => response.json())
        .then(data => {
            state.characterOptions = data;
            state.equipmentSkillsMap = data.equipment_skills_map || {};
            renderProfessionOptions(data.professions);
            renderCharacterEquipmentForm(data.equipment_by_position);
            renderSailorSkillsHint(data.sailor_skills || []);
        })
        .catch(error => console.error('Error loading character options:', error));
}

/**
 * 顯示航海士可加成技能提示
 * @param {string[]} sailorSkills 航海士可加成技能列表
 */
function renderSailorSkillsHint(sailorSkills) {
    const hint = document.getElementById('sailorSkillsHint');
    if (!hint) {
        return;
    }

    if (!sailorSkills.length) {
        hint.innerHTML = '<em>未設定航海士可加成技能</em>';
        return;
    }

    const skillsText = sailorSkills.map(skill => escapeHtml(skill)).join('、');
    hint.innerHTML = `<small>航海士可加成技能：${skillsText}</small>`;
}

/**
 * 將技能映射轉為 HTML 標籤集合
 * @param {Object<string, number>} skills 技能與數值映射
 * @param {boolean} withPlus 是否以 +x 顯示數值
 * @param {string} emptyText 空資料時顯示文字
 * @returns {string} 技能 HTML 內容
 */
function renderSkillItems(skills, withPlus = false, emptyText = '無') {
    const entries = Object.entries(skills || {});
    if (!entries.length) {
        return `<em>${escapeHtml(emptyText)}</em>`;
    }
    return entries
        .map(([skill, level]) => {
            const valueText = withPlus
                ? `+${escapeHtml(level)}`
                : `${escapeHtml(level)}`;
            const highClass = level >= 25 ? ' skill-item--high' : '';
            return `<span class="skill-item${highClass}">${escapeHtml(skill)}(${valueText})</span>`;
        })
        .join('');
}

/**
 * 顯示職業選項
 * @param {Object<string, Object<string, number>>} professions 職業與技能加成映射
 */
function renderProfessionOptions(professions) {
    const select = document.getElementById('professionSelect');
    select.innerHTML = '';

    Object.keys(professions).forEach(profession => {
        const option = document.createElement('option');
        option.value = profession;
        option.textContent = profession;
        select.appendChild(option);
    });
}

/**
 * 顯示配裝選單
 * @param {Object<string, string[]>} equipmentByPosition 位置與裝備名稱列表映射
 */
function renderCharacterEquipmentForm(equipmentByPosition) {
    const leftColumn = document.getElementById('characterLeftSlots');
    const rightColumn = document.getElementById('characterRightSlots');

    if (!leftColumn || !rightColumn) {
        return;
    }

    leftColumn.innerHTML = '';
    rightColumn.innerHTML = '';

    const slotPlan = buildCharacterSlotPlan(equipmentByPosition);

    slotPlan.forEach(slot => {
        const group = document.createElement('div');
        group.className = 'character-slot';

        const label = document.createElement('label');
        label.className = 'character-slot-label';
        label.textContent = slot.label;

        const select = document.createElement('select');
        select.className = 'search-input';
        select.dataset.position = slot.position;

        const emptyOption = document.createElement('option');
        emptyOption.value = '';
        emptyOption.textContent = '不裝備';
        select.appendChild(emptyOption);

        slot.equipmentNames.forEach(name => {
            const option = document.createElement('option');
            option.value = name;
            const skills = state.equipmentSkillsMap[name] || {};
            const skillStr = Object.entries(skills)
                .filter(([, v]) => v)
                .map(([k, v]) => `${k}+${v}`)
                .join(' ');
            option.textContent = skillStr ? `${name} [${skillStr}]` : name;
            select.appendChild(option);
        });

        group.appendChild(label);
        group.appendChild(select);

        if (slot.side === 'right') {
            rightColumn.appendChild(group);
            return;
        }
        leftColumn.appendChild(group);
    });

    setupCharacterAutoCalculate();
}

/**
 * 為職業選單、航海士勾選框與所有裝備下拉選單綁定 change 事件，
 * 讓技能結果在選項變更時即時重新計算。
 */
function setupCharacterAutoCalculate() {
    document.querySelectorAll('#characterEquipmentForm select').forEach(select => {
        select.addEventListener('change', () => {
            updateSlotColor(select);
            calculateCharacterSkills();
        });
        updateSlotColor(select);
    });

    const professionSelect = document.getElementById('professionSelect');
    if (professionSelect) {
        professionSelect.addEventListener('change', calculateCharacterSkills);
    }

    const sailorCheckbox = document.getElementById('sailorCheckbox');
    if (sailorCheckbox) {
        sailorCheckbox.addEventListener('change', calculateCharacterSkills);
    }
}

/**
 * 建立角色配裝欄位配置，讓版面接近建議 UI 圖
 * @param {Object<string, string[]>} equipmentByPosition 位置與裝備名稱列表
 * @returns {Array<{position: string, label: string, equipmentNames: string[], side: string}>}
 */
function buildCharacterSlotPlan(equipmentByPosition) {
    const slots = [];

    Object.entries(equipmentByPosition).forEach(([position, equipmentNames]) => {
        const copyCount = CHARACTER_DUPLICATE_POSITIONS.has(position) ? DUPLICATE_SLOT_COUNT : 1;
        for (let i = 1; i <= copyCount; i++) {
            const slotName = copyCount > 1 ? `${position}${i}` : position;
            slots.push({
                position,
                label: slotName,
                equipmentNames: equipmentNames || [],
                side: CHARACTER_SLOT_SIDE_MAP[slotName]
                    || CHARACTER_SLOT_SIDE_MAP[position]
                    || DEFAULT_SLOT_SIDE
            });
        }
    });

    return slots.sort((a, b) => {
        const aIndex = CHARACTER_SLOT_SIDE_ORDER.findIndex(([slotName]) => slotName === a.label);
        const bIndex = CHARACTER_SLOT_SIDE_ORDER.findIndex(([slotName]) => slotName === b.label);
        if (aIndex !== bIndex) {
            return (aIndex === -1 ? Number.MAX_SAFE_INTEGER : aIndex)
                - (bIndex === -1 ? Number.MAX_SAFE_INTEGER : bIndex);
        }
        return a.label.localeCompare(b.label, 'zh-Hant');
    });
}

/**
 * 收集角色配裝資料並呼叫 API 計算技能
 */
function calculateCharacterSkills() {
    const profession = document.getElementById('professionSelect').value;
    const isSailor = document.getElementById('sailorCheckbox')?.checked || false;
    const equipmentNames = [];

    document.querySelectorAll('#characterEquipmentForm select').forEach(select => {
        if (select.value) {
            equipmentNames.push(select.value);
        }
    });

    fetch('/api/character/calculate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            profession,
            equipment_names: equipmentNames,
            is_sailor: isSailor
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            displayCharacterResults(data);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('計算角色技能失敗');
        });
}

/**
 * 顯示角色技能計算結果（圖形化分欄表格 + 進度條）
 * @param {Object} data 計算結果資料
 */
function displayCharacterResults(data) {
    const container = document.getElementById('characterResults');
    const content = document.getElementById('characterResultsContent');
    const wasHidden = container.style.display === 'none';

    // ── 已選裝備摘要 ──────────────────────────────────────────────────────
    const selectedEquipmentHtml = data.selected_equipment
        .map(eq => `<li><span class="skill-result-pos">${escapeHtml(eq.position)}</span>${escapeHtml(eq.name)}</li>`)
        .join('') || '<li>尚未選擇裝備</li>';

    const invalidEquipmentHtml = (data.invalid_equipment || [])
        .map(name => `<li>${escapeHtml(name)}</li>`)
        .join('');

    // ── 收集所有有值的技能 ────────────────────────────────────────────────
    const allSkills = Array.from(new Set([
        ...Object.keys(data.equipment_skills || {}),
        ...Object.keys(data.profession_bonus || {}),
        ...Object.keys(data.sailor_bonus || {}),
        ...Object.keys(data.skill_caps || {}),
        ...Object.keys(data.highest_skills || {})
    ])).filter(s => (data.highest_skills || {})[s] > 0 || (data.skill_caps || {})[s] > 0)
       .sort((a, b) => ((data.highest_skills || {})[b] || 0) - ((data.highest_skills || {})[a] || 0) || a.localeCompare(b, 'zh-Hant'));

    // ── 最高值的最大值（用於進度條寬度計算）────────────────────────────
    const maxHighest = Math.max(1, ...allSkills.map(s => (data.highest_skills || {})[s] || 0));

    // ── 技能分類（砲術 / 白兵 / 其他）────────────────────────────────────
    function skillCategory(skill) {
        if (CANNON_SKILLS.has(skill)) return 'cannon';
        if (BOARDING_SKILLS.has(skill)) return 'boarding';
        return '';
    }

    function cell(val) {
        if (!val) return '<td class="skill-table-zero">-</td>';
        return `<td>${escapeHtml(String(val))}</td>`;
    }

    // ── 生成表格行 ────────────────────────────────────────────────────────
    const rows = allSkills.map(skill => {
        const eq     = (data.equipment_skills  || {})[skill] || 0;
        const prof   = (data.profession_bonus  || {})[skill] || 0;
        const sailor = (data.sailor_bonus      || {})[skill] || 0;
        const bonus  = (data.bonus_skills      || {})[skill] || 0;
        const cap    = (data.skill_caps        || {})[skill] || 0;
        const high   = (data.highest_skills   || {})[skill] || 0;

        const cat    = skillCategory(skill);
        const rowCls = cat ? ` class="skill-row-${cat}"` : '';
        const pct    = Math.round((high / maxHighest) * 100);

        const barHtml = `
            <td class="skill-bar-cell">
                <div class="skill-bar-wrap">
                    <div class="skill-bar skill-bar-${cat || 'neutral'}" style="width:${pct}%"></div>
                    <span class="skill-bar-label">${escapeHtml(String(high))}</span>
                </div>
            </td>`;

        return `<tr${rowCls}>
            <td class="skill-name-cell">${escapeHtml(skill)}</td>
            ${cell(eq || 0)}
            ${cell(prof || 0)}
            ${cell(sailor || 0)}
            ${cell(bonus || 0)}
            ${cell(cap || 0)}
            ${barHtml}
        </tr>`;
    }).join('');

    const tableHtml = allSkills.length
        ? `<table class="skill-result-table">
            <thead>
                <tr>
                    <th>技能</th>
                    <th title="裝備加成">裝備</th>
                    <th title="職業加成">職業</th>
                    <th title="航海士加成">航海士</th>
                    <th title="加成小計">加成</th>
                    <th title="角色上限">上限</th>
                    <th title="角色上限 + 加成小計">最高值</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
           </table>`
        : '<p>（目前沒有技能加成）</p>';

    // ── 組合最終 HTML ─────────────────────────────────────────────────────
    content.innerHTML = `
        <div class="character-summary">
            <div class="char-info-row">
                <span class="char-info-label">職業</span>
                <span class="char-info-val">${escapeHtml(data.profession)}</span>
                <span class="char-info-label">航海士</span>
                <span class="char-info-val ${data.is_sailor ? 'sailor-on' : ''}">${data.is_sailor ? '✔ 是' : '否'}</span>
            </div>
            <div class="char-selected-label"><strong>已選裝備：</strong></div>
            <ul class="char-selected-list">${selectedEquipmentHtml}</ul>
            ${invalidEquipmentHtml ? `<div class="error">未找到裝備：<ul>${invalidEquipmentHtml}</ul></div>` : ''}
        </div>
    `;

    // ── 技能分解總覽放在頁面最下方 ───────────────────────────────────────
    const breakdownSection = document.getElementById('skillBreakdownSection');
    if (breakdownSection) {
        breakdownSection.innerHTML = `
            <h4>技能分解總覽</h4>
            <div class="skill-legend">
                <span class="skill-legend-item legend-cannon">■ 砲術系</span>
                <span class="skill-legend-item legend-boarding">■ 白兵系</span>
            </div>
            ${tableHtml}
        `;
        breakdownSection.style.display = 'block';
    }

    container.style.display = 'block';
    if (wasHidden) {
        container.scrollIntoView({ behavior: 'smooth' });
    }
}

// 顯示統計信息
function displayStats(stats) {
    const statsContent = document.getElementById('statsContent');
    
    let html = `
        <div class="stat-card">
            <div class="stat-card-label">總裝備數</div>
            <div class="stat-card-value">${stats.total_equipment}</div>
        </div>
        <div class="stat-card">
            <div class="stat-card-label">位置類型</div>
            <div class="stat-card-value">${stats.positions.length}</div>
        </div>
        <div class="stat-card">
            <div class="stat-card-label">技能種類</div>
            <div class="stat-card-value">${stats.skills.length}</div>
        </div>
    `;
    
    statsContent.innerHTML = html;
    
    // 添加按位置的統計列表
    const listDiv = document.createElement('div');
    listDiv.className = 'stat-list';
    listDiv.innerHTML = '<h3>各位置的裝備數</h3>';
    
    const listContent = document.createElement('div');
    Object.entries(stats.equipment_by_position).forEach(([pos, count]) => {
        const item = document.createElement('div');
        item.className = 'stat-list-item';
        item.innerHTML = `<span>${pos}</span><strong>${count} 件</strong>`;
        listContent.appendChild(item);
    });
    
    listDiv.appendChild(listContent);
    statsContent.appendChild(listDiv);
}

// ── 自動配裝功能 ──────────────────────────────────────────────────────────

// Must match the 5 autoPriority<N> select IDs declared in index.html
const AUTO_PRIORITY_IDS = ['autoPriority1', 'autoPriority2', 'autoPriority3', 'autoPriority4', 'autoPriority5'];

/**
 * 綁定自動配裝觸發按鈕與結果區域的事件監聽器（使用事件委派）
 */
function setupAutoBuilderListeners() {
    const triggerBtn = document.getElementById('autoTriggerBtn');
    if (triggerBtn) {
        triggerBtn.addEventListener('click', triggerAutoBuild);
    }

    // 事件委派：一鍵套用技能組合的按鈕
    const presetRow = document.querySelector('.auto-build-preset-row');
    if (presetRow) {
        presetRow.addEventListener('click', function (e) {
            const btn = e.target.closest('.auto-preset-btn');
            if (btn) {
                applySkillPreset(btn.dataset.preset);
            }
        });
    }

    // 事件委派：捕捉結果表格中各方案的「套用」按鈕
    const resultsDiv = document.getElementById('autoBuildResults');
    if (resultsDiv) {
        resultsDiv.addEventListener('click', function (e) {
            const btn = e.target.closest('.auto-build-apply-btn');
            if (btn) {
                applyAutoBuildPlan(parseInt(btn.dataset.planIndex, 10));
            }
        });
    }
}

/**
 * 初始化自動配裝優先技能下拉選單
 * @param {string[]} skills 所有技能列表
 */
function renderAutoBuildSkillDropdowns(skills) {
    const groups = groupSkillsForDropdown(skills);
    AUTO_PRIORITY_IDS.forEach(id => {
        const select = document.getElementById(id);
        if (!select) return;
        // 保留第一個「（不選）」，其餘（含 optgroup）整個重建
        while (select.lastElementChild && select.lastElementChild !== select.firstElementChild) {
            select.removeChild(select.lastElementChild);
        }
        groups.forEach(([label, members]) => {
            const group = document.createElement('optgroup');
            group.label = label;
            members.forEach(skill => {
                const opt = document.createElement('option');
                opt.value = skill;
                opt.textContent = skill;
                group.appendChild(opt);
            });
            select.appendChild(group);
        });
        select.addEventListener('change', refreshAutoBuildSkillOptions);
    });
}

/**
 * 依 SKILL_GROUPS 將技能分組供 optgroup 使用
 * 不在分類表內的技能一律歸「其他」，避免資料源新增技能時從下拉中消失
 * @param {string[]} skills 所有技能列表
 * @returns {Array<[string, string[]]>} [分類名稱, 該類技能] 陣列
 */
function groupSkillsForDropdown(skills) {
    const available = new Set(skills);
    const groups = SKILL_GROUPS
        .map(([label, members]) => [label, members.filter(s => available.has(s))])
        .filter(([, members]) => members.length > 0);

    const classified = new Set(SKILL_GROUPS.flatMap(([, members]) => members));
    const rest = skills.filter(s => !classified.has(s));
    if (rest.length) groups.push(['其他', rest]);
    return groups;
}

/**
 * 套用一鍵技能組合：填入前 N 個優先技能欄位、其餘清空，並立即執行自動配裝
 * @param {string} presetName 組合名稱（對應按鈕的 data-preset）
 */
function applySkillPreset(presetName) {
    const preset = SKILL_PRESETS.find(([label]) => label === presetName);
    if (!preset) return;

    const [, members] = preset;
    AUTO_PRIORITY_IDS.forEach((id, index) => {
        const select = document.getElementById(id);
        if (!select) return;
        select.value = members[index] || '';
    });
    refreshAutoBuildSkillOptions();
    triggerAutoBuild();
}

/**
 * 重新整理各優先技能下拉選單的可用選項，防止重複選擇
 */
function refreshAutoBuildSkillOptions() {
    const selectedValues = AUTO_PRIORITY_IDS.map(id => {
        const el = document.getElementById(id);
        return el ? el.value : '';
    }).filter(v => v);

    AUTO_PRIORITY_IDS.forEach(id => {
        const select = document.getElementById(id);
        if (!select) return;
        const currentVal = select.value;
        const othersSelected = selectedValues.filter(v => v !== currentVal);
        Array.from(select.options).forEach(opt => {
            opt.disabled = opt.value ? othersSelected.includes(opt.value) : false;
        });
    });
}

/**
 * 執行自動配裝：收集選項並呼叫 API
 */
function triggerAutoBuild() {
    const prioritySkills = AUTO_PRIORITY_IDS
        .map(id => { const el = document.getElementById(id); return el ? el.value : ''; })
        .filter(v => v);

    if (!prioritySkills.length) {
        alert('請至少選擇一個優先技能');
        return;
    }

    const profession = document.getElementById('professionSelect').value || '通用';
    const isSailor = document.getElementById('sailorCheckbox')?.checked || false;
    const skillCap = parseInt(document.getElementById('autoSkillCap').value, 10) || 25;
    const excludeQuality = document.getElementById('autoPoorMode')?.checked || false;

    const resultsDiv = document.getElementById('autoBuildResults');
    resultsDiv.innerHTML =
        '<div class="auto-build-loading"><span class="auto-build-spinner"></span>計算最佳配裝中…</div>';
    resultsDiv.style.display = 'block';

    fetch('/api/character/suggest-builds', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            profession,
            priority_skills: prioritySkills,
            is_sailor: isSailor,
            top_n: 5,
            candidates_per_slot: 3,
            skill_cap: skillCap,
            exclude_quality: excludeQuality
        })
    })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                resultsDiv.innerHTML = `<p class="error">${escapeHtml(data.error)}</p>`;
                return;
            }
            displayAutoBuildResults(data.plans, prioritySkills);
        })
        .catch(err => {
            console.error(err);
            resultsDiv.innerHTML = '<p class="error">自動配裝失敗，請稍後再試</p>';
        });
}

/**
 * 顯示自動配裝建議方案
 * @param {Array} plans 方案列表
 * @param {string[]} prioritySkills 優先技能
 */
function displayAutoBuildResults(plans, prioritySkills) {
    state.autoBuildPlans = plans;
    const container = document.getElementById('autoBuildResults');

    if (!plans || !plans.length) {
        container.innerHTML = '<p class="error">找不到符合條件的配裝方案</p>';
        container.style.display = 'block';
        return;
    }

    // 數值是「最高值」（角色上限＋加成），超過遊戲上限的部分不列入，需標示清楚
    const skillCols = prioritySkills
        .map(s => `<th title="最高值：角色上限＋加成，超過上限以上限計">${escapeHtml(s)}</th>`)
        .join('');
    // data-label 供手機版把表格轉成卡片時顯示欄位名（CSS ::before 取用）
    // 標籤：照使用者優先順序最佳的那套 vs 生效總和最高的那套（可能是同一套）
    const totalOf = p => Object.values(p.priority_values || {}).reduce((a, b) => a + b, 0);
    const maxTotal = Math.max(...plans.map(totalOf));
    let overallMarked = false;

    const rows = plans.map((plan, i) => {
        const tags = [];
        if (plan.by_priority_order) tags.push('順序最高');
        if (!overallMarked && totalOf(plan) === maxTotal) {
            tags.push('綜合最高');
            overallMarked = true;
        }
        const tagHtml = tags
            .map(t => `<span class="auto-build-tag auto-build-tag-${t === '順序最高' ? 'order' : 'overall'}">${t}</span>`)
            .join('');
        const skillVals = prioritySkills
            .map(s => `<td class="auto-build-skill-cell" data-label="${escapeHtml(s)}">${escapeHtml(String(plan.priority_values[s] || 0))}</td>`)
            .join('');
        const eqList = plan.equipment_names.map(e => escapeHtml(e)).join('、');
        return `<tr>
            <td class="auto-build-plan-cell">方案 ${i + 1}${tagHtml}</td>
            ${skillVals}
            <td class="auto-build-eq-cell" data-label="裝備">${eqList}</td>
            <td class="auto-build-action-cell"><button class="btn btn-primary auto-build-apply-btn" data-plan-index="${i}">套用</button></td>
        </tr>`;
    }).join('');

    container.innerHTML = `
        <div class="auto-build-results-header">
            共 ${plans.length} 套方案　優先技能：${prioritySkills.map(s => escapeHtml(s)).join(' ＞ ')}
        </div>
        <table class="auto-build-table">
            <thead>
                <tr>
                    <th>方案</th>
                    ${skillCols}
                    <th>裝備清單</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>
        <p class="auto-build-hint">點擊「套用」可將方案填入角色配裝欄位</p>
    `;
    container.style.display = 'block';
    container.scrollIntoView({ behavior: 'smooth' });
}

/**
 * 將自動配裝方案套用至角色配裝欄位
 * @param {number} index 方案索引
 */
function applyAutoBuildPlan(index) {
    const plans = state.autoBuildPlans;
    if (!plans || index >= plans.length) return;
    const equipmentNames = plans[index].equipment_names;

    // 建立裝備名稱 → 位置對應表（由 character options 取得）
    const nameToPos = {};
    if (state.characterOptions && state.characterOptions.equipment_by_position) {
        Object.entries(state.characterOptions.equipment_by_position).forEach(([pos, names]) => {
            names.forEach(name => { nameToPos[name] = pos; });
        });
    }

    // 建立位置 → 待分配裝備名稱清單
    const posToNames = {};
    equipmentNames.forEach(name => {
        const pos = nameToPos[name];
        if (pos) {
            if (!posToNames[pos]) posToNames[pos] = [];
            posToNames[pos].push(name);
        }
    });

    // 依序分配至各槽位選單
    const posAssigned = {};
    document.querySelectorAll('#characterEquipmentForm select').forEach(sel => {
        const pos = sel.dataset.position;
        const names = posToNames[pos] || [];
        const idx = posAssigned[pos] || 0;

        if (idx < names.length) {
            sel.value = names[idx];
            posAssigned[pos] = idx + 1;
        } else {
            sel.value = '';
        }
        updateSlotColor(sel);
    });

    calculateCharacterSkills();
    document.getElementById('characterEquipmentForm').scrollIntoView({ behavior: 'smooth' });
}
