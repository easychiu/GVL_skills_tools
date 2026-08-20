// GVL 裝備表 GitHub Pages API 墊片（shim）
//
// 目的：讓 gvl_app/static/script.js 在沒有 Flask 後端的 GitHub Pages 上原樣運作。
// 作法：載入同目錄的 data.json，並覆寫 window.fetch —— 只要請求路徑含 /api/，
// 就在本地依 data.json 算出與 gvl_app/app.py 相同的回應；其餘請求原封不動轉給
// 原生 fetch。本檔案務必在 script.js 之前載入。
//
// 注意：Pages 站台可能部署在子路徑（如 /GVL_skills_tools/），而 script.js 用的是
// 絕對路徑 /api/xxx，所以攔截時只看 pathname 裡 /api/ 之後的部分，不假設站台在根目錄。
(function () {
    'use strict';

    const originalFetch = window.fetch.bind(window);

    // data.json 只在此載入一次，之後所有 /api/ 請求共用同一個 Promise。
    // 用 document.baseURI 解析，確保子路徑部署時仍能找到同目錄的 data.json。
    const dataUrl = new URL('data.json', document.baseURI).href;
    const dataPromise = originalFetch(dataUrl).then(res => {
        if (!res.ok) {
            throw new Error(`data.json 載入失敗：HTTP ${res.status}`);
        }
        return res.json();
    });

    // script.js 對 fetch 失敗只做 console.error，資料載不到時畫面會是空白且毫無提示，
    // 因此在此補一條可見橫幅，讓使用者知道要重新整理或回報。
    dataPromise.catch(err => {
        const showBanner = () => {
            const bar = document.createElement('div');
            bar.textContent = `資料載入失敗，請重新整理頁面。（${err.message}）`;
            bar.style.cssText =
                'background:#c0392b;color:#fff;padding:12px;text-align:center;font-weight:bold';
            document.body.prepend(bar);
        };
        if (document.body) {
            showBanner();
        } else {
            document.addEventListener('DOMContentLoaded', showBanner);
        }
    });

    // 裝備名稱 → 裝備物件索引，首次用到時才建立（suggest-builds 會大量查詢）。
    let equipmentIndex = null;

    /**
     * 取得裝備名稱索引（Map），用於 O(1) 依名稱查裝備。
     * @param {Object} data data.json 內容
     * @returns {Map<string, Object>}
     */
    function getEquipmentIndex(data) {
        if (!equipmentIndex) {
            // 同名裝備必須取第一筆，才與 data_handler.get_equipment_by_name 的線性查找一致
            // （new Map(entries) 是後蓋前，會取到最後一筆）
            equipmentIndex = new Map();
            for (const eq of data.equipment) {
                if (!equipmentIndex.has(eq.name)) {
                    equipmentIndex.set(eq.name, eq);
                }
            }
        }
        return equipmentIndex;
    }

    // ── 通用工具 ──────────────────────────────────────────────────────────

    /**
     * 依 Unicode 碼位比較字串（等同 Python 預設字串排序）。
     * 注意：不可用 localeCompare，中文會依筆劃/拼音排序，結果會與後端不同。
     * @param {string} a
     * @param {string} b
     * @returns {number}
     */
    function zhCompare(a, b) {
        return a < b ? -1 : a > b ? 1 : 0;
    }

    /**
     * 回傳依 zhCompare 排序後的新陣列（不改動原陣列）。
     * @param {string[]} arr
     * @returns {string[]}
     */
    function zhSort(arr) {
        return (arr || []).slice().sort(zhCompare);
    }

    /**
     * 排序技能映射：先按數值由大到小，同分時按技能名稱升冪（同 _sort_skill_map）。
     * @param {Object<string, number>} skillMap
     * @returns {Object<string, number>}
     */
    function sortSkillMap(skillMap) {
        const entries = Object.entries(skillMap || {});
        entries.sort((a, b) => (b[1] - a[1]) || zhCompare(a[0], b[0]));
        return Object.fromEntries(entries);
    }

    /**
     * 逐項比較兩個數字陣列（字典序），用於 score_key / _score 這類 tuple 排序。
     * @param {number[]} a
     * @param {number[]} b
     * @returns {number}
     */
    function compareTuples(a, b) {
        const len = Math.max(a.length, b.length);
        for (let i = 0; i < len; i++) {
            const diff = (a[i] ?? 0) - (b[i] ?? 0);
            if (diff !== 0) return diff;
        }
        return 0;
    }

    /**
     * 模擬 Python int() 轉換語意：僅接受整數（數字、布林、純整數字串，可含前後空白與正負號）。
     * @param {*} value
     * @returns {number}
     * @throws {Error} 無法轉換時拋出
     */
    function toPyInt(value) {
        if (typeof value === 'number') {
            if (!Number.isFinite(value)) throw new Error('invalid int');
            return Math.trunc(value);
        }
        if (typeof value === 'boolean') {
            return value ? 1 : 0;
        }
        if (typeof value === 'string' && /^\s*[+-]?\d+\s*$/.test(value)) {
            return parseInt(value, 10);
        }
        throw new Error('invalid int');
    }

    /**
     * 讀取查詢參數並轉為整數；缺少或無法轉換時回傳預設值（同 Flask type=int 行為）。
     * @param {URLSearchParams} searchParams
     * @param {string} name
     * @param {number} defaultValue
     * @returns {number}
     */
    function queryInt(searchParams, name, defaultValue) {
        const raw = searchParams.get(name);
        if (raw === null) return defaultValue;
        try {
            return toPyInt(raw);
        } catch {
            return defaultValue;
        }
    }

    /** 建立 API 錯誤物件（不用 class，維持極簡） */
    function apiError(status, message) {
        return { isApiError: true, status, message };
    }

    /** 包成標準 JSON Response，同 Flask jsonify 的輸出格式 */
    function jsonResponse(body, status = 200) {
        return new Response(JSON.stringify(body), {
            status,
            headers: { 'Content-Type': 'application/json' }
        });
    }

    /**
     * 解析 POST 請求的 JSON body；空 body 視為 {}，格式錯誤則拋出 400 錯誤。
     * @param {string|Request} input fetch 的第一參數
     * @param {Object} [init] fetch 的第二參數
     * @returns {Promise<Object>}
     */
    async function parseJsonBody(input, init) {
        let bodyText = '';
        if (init && typeof init.body === 'string') {
            bodyText = init.body;
        } else if (input instanceof Request) {
            bodyText = await input.text();
        }

        if (!bodyText.trim()) {
            return {};
        }
        try {
            return JSON.parse(bodyText);
        } catch {
            throw apiError(400, 'JSON 格式錯誤');
        }
    }

    /** 檢查 payload 是否為一般 JSON 物件（非陣列、非 null） */
    function requireJsonObject(payload) {
        if (typeof payload !== 'object' || payload === null || Array.isArray(payload)) {
            throw apiError(400, '請提供 JSON 物件');
        }
        return payload;
    }

    // ── 角色技能計算（移植 GVLDataHandler.calculate_character_skills） ──────

    /**
     * 計算角色總技能（裝備 + 職業 + 航海士）。
     * @param {Object} data data.json 內容
     * @param {string} profession 職業名稱
     * @param {string[]} equipmentNames 裝備名稱列表
     * @param {boolean} isSailor 是否套用航海士 +1
     * @returns {Object} 同 app.py /api/character/calculate 的回應內容
     */
    function calcCharacterSkills(data, profession, equipmentNames, isSailor) {
        const professions = data.professions || {};
        if (!Object.prototype.hasOwnProperty.call(professions, profession)) {
            throw apiError(400, `不支持的職業: ${profession}`);
        }

        const professionBonus = professions[profession] || {};
        const skillCapsByProfession = data.skill_caps || {};
        const skillCaps = skillCapsByProfession[profession] ?? skillCapsByProfession['通用'] ?? {};

        const index = getEquipmentIndex(data);
        const equipmentSkills = {};
        const selectedEquipment = [];
        const invalidEquipment = [];

        for (const name of equipmentNames) {
            const eq = index.get(name);
            if (!eq) {
                invalidEquipment.push(name);
                continue;
            }
            selectedEquipment.push({ position: eq.position, name: eq.name });
            for (const [skill, level] of Object.entries(eq.skills || {})) {
                equipmentSkills[skill] = (equipmentSkills[skill] || 0) + level;
            }
        }

        const sailorBonus = {};
        if (isSailor) {
            for (const skill of (data.sailor_skills || [])) {
                sailorBonus[skill] = 1;
            }
        }

        const bonusSkills = {};
        const bonusKeys = new Set([
            ...Object.keys(equipmentSkills),
            ...Object.keys(professionBonus),
            ...Object.keys(sailorBonus)
        ]);
        for (const skill of bonusKeys) {
            bonusSkills[skill] =
                (equipmentSkills[skill] || 0) + (professionBonus[skill] || 0) + (sailorBonus[skill] || 0);
        }

        const highestSkills = {};
        const highestKeys = new Set([...Object.keys(skillCaps), ...Object.keys(bonusSkills)]);
        for (const skill of highestKeys) {
            highestSkills[skill] = (skillCaps[skill] || 0) + (bonusSkills[skill] || 0);
        }

        return {
            profession,
            is_sailor: isSailor,
            selected_equipment: selectedEquipment,
            invalid_equipment: invalidEquipment,
            equipment_skills: sortSkillMap(equipmentSkills),
            profession_bonus: sortSkillMap(professionBonus),
            sailor_bonus: sortSkillMap(sailorBonus),
            skill_caps: sortSkillMap(skillCaps),
            bonus_skills: sortSkillMap(bonusSkills),
            highest_skills: sortSkillMap(highestSkills)
        };
    }

    // ── 自動配裝（移植 GVLDataHandler.suggest_builds） ───────────────────────

    const SUGGEST_DUPLICATE_POSITIONS = new Set(['飾品', '寶物']);
    const SUGGEST_SLOT_ORDER = ['飾品1', '飾品2', '寶物1', '寶物2', '主武', '副武', '頭盔', '衣服', '手套', '鞋子'];
    const SUGGEST_PRIORITY_TARGET = 25;

    /**
     * 裝備優先技能評分：[覆蓋的優先技能數, 優先技能加成總和, 該裝備所有技能加成總和]。
     * @param {Object} eq 裝備物件
     * @param {string[]} pSkills 優先技能清單
     * @returns {number[]}
     */
    function scoreEquipmentForPriority(eq, pSkills) {
        const sk = eq.skills || {};
        const pvals = pSkills.map(s => sk[s] || 0);
        const covered = pvals.filter(v => v > 0).length;
        const totalPval = pvals.reduce((a, b) => a + b, 0);
        const totalAll = Object.values(sk).reduce((a, b) => a + b, 0);
        return [covered, totalPval, totalAll];
    }

    /**
     * 產生笛卡兒積，枚舉順序與 Python itertools.product 相同（最後一軸變動最快）。
     * @param {Array[]} lists
     */
    function* cartesianProduct(lists) {
        const lens = lists.map(l => l.length);
        if (lens.some(l => l === 0)) return;
        const idx = new Array(lists.length).fill(0);
        while (true) {
            yield idx.map((v, i) => lists[i][v]);
            let pos = lists.length - 1;
            while (pos >= 0) {
                idx[pos] += 1;
                if (idx[pos] < lens[pos]) break;
                idx[pos] = 0;
                pos -= 1;
            }
            if (pos < 0) break;
        }
    }

    /**
     * 根據優先技能搜尋最佳 Top-N 配裝方案（邏輯移植自 suggest_builds，細節見 data_handler.py）。
     * @param {Object} data data.json 內容
     * @param {Object} opts
     * @returns {Array<Object>} 方案列表
     */
    function suggestBuilds(data, opts) {
        const { profession, prioritySkills, isSailor, topN, candidatesPerSlot, skillCap, excludeQuality } = opts;

        // 只保留有效且不重複技能（最多 5 個，保留輸入順序）
        const validSkills = data.skills || [];
        const pSkills = [];
        for (const skill of prioritySkills) {
            if (!skill) continue;
            if (!validSkills.includes(skill)) continue;
            if (pSkills.includes(skill)) continue;
            pSkills.push(skill);
            if (pSkills.length >= 5) break;
        }

        // 建立各位置已排序裝備清單（可選擇排除「(質變)」裝備）
        const sortedPositions = zhSort(data.positions || []);
        const eqByPos = {};
        for (const pos of sortedPositions) {
            let eqList = data.equipment.filter(e => e.position === pos);
            if (excludeQuality) {
                eqList = eqList.filter(e => !e.name.includes('(質變)'));
            }
            eqByPos[pos] = eqList.slice().sort((a, b) => zhCompare(a.name, b.name));
        }

        // 展開雙槽位（飾品/寶物各兩個），並依 SUGGEST_SLOT_ORDER 排序
        const slots = [];
        for (const pos of sortedPositions) {
            const equipment = eqByPos[pos];
            const count = SUGGEST_DUPLICATE_POSITIONS.has(pos) ? 2 : 1;
            for (let i = 1; i <= count; i++) {
                const label = count > 1 ? `${pos}${i}` : pos;
                slots.push({ label, equipment });
            }
        }
        const orderMap = new Map(SUGGEST_SLOT_ORDER.map((s, idx) => [s, idx]));
        slots.sort((a, b) => (orderMap.get(a.label) ?? 999) - (orderMap.get(b.label) ?? 999));

        // 每槽保留 Top-K 候選（依 _score 降冪排序）；空位置以 null 佔位
        const slotCandidates = slots.map(slot => {
            if (!slot.equipment.length) return [null];
            const scored = slot.equipment
                .slice()
                .sort((a, b) =>
                    compareTuples(scoreEquipmentForPriority(b, pSkills), scoreEquipmentForPriority(a, pSkills))
                );
            return scored.slice(0, candidatesPerSlot);
        });

        // 枚舉所有組合：過濾重複的「(唯一)」裝備，並以排序後名稱簽章去重
        const uniqueCombos = [];
        const seenSig = new Set();
        for (const combo of cartesianProduct(slotCandidates)) {
            const eqNames = combo.filter(eq => eq !== null).map(eq => eq.name);
            // 唯一裝備只會有一件，質變版與原版視為同一件（去掉「(質變)」後比對）
            const uniqueOnly = eqNames
                .filter(n => n.includes('(唯一)'))
                .map(n => n.replace('(質變)', ''));
            if (uniqueOnly.length !== new Set(uniqueOnly).size) continue;
            // 簽章分隔符是 NUL（非空白）：裝備名稱不可能含 NUL，串接後不會與其他組合碰撞
            const sig = eqNames.slice().sort(zhCompare).join('\u0000');
            if (seenSig.has(sig)) continue;
            seenSig.add(sig);
            uniqueCombos.push(eqNames);
        }

        // 逐組合計算技能、依 skill_cap 過濾，再依 score_key 評分
        const results = [];
        for (const eqNames of uniqueCombos) {
            const skillResult = calcCharacterSkills(data, profession, eqNames, isSailor);
            const bonusSkills = skillResult.bonus_skills || {};
            if (skillCap > 0 && Object.values(bonusSkills).some(v => v > skillCap)) continue;

            const priorityValues = {};
            for (const skill of pSkills) priorityValues[skill] = bonusSkills[skill] || 0;

            const priorityScore = pSkills.map(
                skill => SUGGEST_PRIORITY_TARGET - Math.abs((priorityValues[skill] || 0) - SUGGEST_PRIORITY_TARGET)
            );
            const priorityClosenessTotal = priorityScore.reduce((a, b) => a + b, 0);
            const priorityRawTotal = Object.values(priorityValues).reduce((a, b) => a + b, 0);
            const totalBonus = Object.values(bonusSkills).reduce((a, b) => a + b, 0);
            const skillsAtCap = pSkills.filter(
                skill => (priorityValues[skill] || 0) >= SUGGEST_PRIORITY_TARGET
            ).length;

            const scoreKey = [skillsAtCap, priorityClosenessTotal, ...priorityScore, priorityRawTotal, totalBonus];

            results.push({
                equipment_names: eqNames,
                score_key: scoreKey,
                priority_values: priorityValues,
                skill_result: skillResult
            });
        }

        results.sort((a, b) => compareTuples(b.score_key, a.score_key));
        return results.slice(0, topN);
    }

    // ── 9 個 API 端點 ─────────────────────────────────────────────────────

    function apiPositions(data) {
        const positions = zhSort(data.positions);
        return jsonResponse({ positions, count: positions.length });
    }

    function apiSkills(data) {
        const skills = zhSort(data.skills);
        return jsonResponse({ skills, count: skills.length });
    }

    function apiSearch(data, searchParams) {
        const query = (searchParams.get('q') || '').trim();
        const searchType = searchParams.get('type') ?? 'name';

        if (!query) {
            throw apiError(400, '搜索關鍵字不能為空');
        }

        let results;
        if (searchType === 'name') {
            const keyword = query.toLowerCase();
            results = data.equipment.filter(eq => eq.name.toLowerCase().includes(keyword));
        } else if (searchType === 'skill') {
            const minLevel = queryInt(searchParams, 'min_level', 1);
            results = data.equipment.filter(
                eq => (eq.skills || {})[query] !== undefined && eq.skills[query] >= minLevel
            );
        } else if (searchType === 'position') {
            results = data.equipment.filter(eq => eq.position === query);
        } else {
            throw apiError(400, '不支持的搜索類型');
        }

        return jsonResponse({ query, type: searchType, count: results.length, results });
    }

    function apiEquipment(data, searchParams) {
        const page = queryInt(searchParams, 'page', 1);
        const perPage = queryInt(searchParams, 'per_page', 20);
        const start = (page - 1) * perPage;
        const end = start + perPage;
        const total = data.equipment.length;

        return jsonResponse({
            equipment: data.equipment.slice(start, end),
            page,
            per_page: perPage,
            total,
            pages: Math.ceil(total / perPage)
        });
    }

    function apiConfig(data, rawName) {
        const name = decodeURIComponent(rawName);
        const configs = data.configs || {};
        if (!Object.prototype.hasOwnProperty.call(configs, name)) {
            throw apiError(404, '配置未找到');
        }
        return jsonResponse({ name, config: configs[name] });
    }

    function apiStats(data) {
        return jsonResponse(data.stats || {});
    }

    function apiCharacterOptions(data) {
        const positions = zhSort(data.positions);

        const equipmentByPosition = {};
        for (const pos of positions) {
            const names = data.equipment.filter(eq => eq.position === pos).map(eq => eq.name);
            equipmentByPosition[pos] = zhSort(names);
        }

        const equipmentSkillsMap = {};
        for (const eq of data.equipment) {
            equipmentSkillsMap[eq.name] = eq.skills || {};
        }

        return jsonResponse({
            positions,
            equipment_by_position: equipmentByPosition,
            equipment_skills_map: equipmentSkillsMap,
            professions: data.professions || {},
            sailor_skills: zhSort(data.sailor_skills)
        });
    }

    async function apiCharacterCalculate(data, input, init) {
        const payload = requireJsonObject(await parseJsonBody(input, init));
        const profession = payload.profession ?? '通用';
        const equipmentNames = payload.equipment_names ?? [];
        const isSailor = Boolean(payload.is_sailor ?? false);

        if (!Array.isArray(equipmentNames)) {
            throw apiError(400, 'equipment_names 必須為陣列');
        }

        const result = calcCharacterSkills(data, profession, equipmentNames, isSailor);
        return jsonResponse(result);
    }

    async function apiCharacterSuggestBuilds(data, input, init) {
        const payload = requireJsonObject(await parseJsonBody(input, init));
        const profession = payload.profession ?? '通用';
        const prioritySkills = payload.priority_skills ?? [];
        const isSailor = Boolean(payload.is_sailor ?? false);
        const excludeQuality = Boolean(payload.exclude_quality ?? false);

        if (!Array.isArray(prioritySkills)) {
            throw apiError(400, 'priority_skills 必須為陣列');
        }
        if (!prioritySkills.length) {
            throw apiError(400, 'priority_skills 不可為空');
        }
        if (!Object.prototype.hasOwnProperty.call(data.professions || {}, profession)) {
            throw apiError(400, `不支持的職業: ${profession}`);
        }

        let topN = payload.top_n ?? 5;
        let candidatesPerSlot = payload.candidates_per_slot ?? 3;
        let skillCap = payload.skill_cap ?? 25;
        try {
            topN = toPyInt(topN);
            candidatesPerSlot = toPyInt(candidatesPerSlot);
            skillCap = toPyInt(skillCap);
        } catch {
            throw apiError(400, 'top_n、candidates_per_slot、skill_cap 必須為整數');
        }

        if (topN < 1 || candidatesPerSlot < 1 || skillCap < 0) {
            throw apiError(400, 'top_n、candidates_per_slot 必須 >= 1，skill_cap 必須 >= 0');
        }

        const plans = suggestBuilds(data, {
            profession,
            prioritySkills,
            isSailor,
            topN,
            candidatesPerSlot,
            skillCap,
            excludeQuality
        });

        return jsonResponse({
            profession,
            priority_skills: prioritySkills,
            count: plans.length,
            plans
        });
    }

    // ── 路由分派 ──────────────────────────────────────────────────────────

    /**
     * 依 method + route 分派至對應端點處理函式。
     * @param {string} route pathname 中 /api/ 之後的部分
     * @param {string} method HTTP 方法（大寫）
     * @param {URLSearchParams} searchParams
     * @param {string|Request} input 原始 fetch 第一參數
     * @param {Object} [init] 原始 fetch 第二參數
     * @param {Object} data data.json 內容
     * @returns {Promise<Response>}
     */
    async function dispatchApi(route, method, searchParams, input, init, data) {
        if (method === 'GET') {
            if (route === 'positions') return apiPositions(data);
            if (route === 'skills') return apiSkills(data);
            if (route === 'search') return apiSearch(data, searchParams);
            if (route === 'equipment') return apiEquipment(data, searchParams);
            if (route.startsWith('config/')) return apiConfig(data, route.slice('config/'.length));
            if (route === 'stats') return apiStats(data);
            if (route === 'character/options') return apiCharacterOptions(data);
        }
        if (method === 'POST') {
            if (route === 'character/calculate') return apiCharacterCalculate(data, input, init);
            if (route === 'character/suggest-builds') return apiCharacterSuggestBuilds(data, input, init);
        }
        return jsonResponse({ error: '頁面未找到' }, 404);
    }

    // ── window.fetch 覆寫 ─────────────────────────────────────────────────

    window.fetch = async function (input, init) {
        let url;
        try {
            const urlStr = typeof input === 'string' ? input : input instanceof Request ? input.url : String(input);
            url = new URL(urlStr, document.baseURI);
        } catch {
            return originalFetch(input, init);
        }

        const marker = '/api/';
        const markerIndex = url.pathname.indexOf(marker);
        if (markerIndex === -1) {
            return originalFetch(input, init);
        }

        const route = url.pathname.slice(markerIndex + marker.length);
        const method = ((init && init.method) || (input instanceof Request && input.method) || 'GET').toUpperCase();

        const data = await dataPromise;

        try {
            return await dispatchApi(route, method, url.searchParams, input, init, data);
        } catch (err) {
            if (err && err.isApiError) {
                return jsonResponse({ error: err.message }, err.status);
            }
            throw err;
        }
    };
})();
