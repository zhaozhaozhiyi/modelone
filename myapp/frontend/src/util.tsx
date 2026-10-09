/**
 * 获取第一个表格的可视化高度
 * * @param {number} extraHeight 额外的高度(表格底部的内容高度 Number类型,默认为74)
 * @param {reactRef} ref Table所在的组件的ref
 */
export function getTableScroll({ extraHeight, ref }: any = {}) {
    if (typeof extraHeight == "undefined") {
        //  默认底部分页64 + 边距10
        extraHeight = 74
    }
    let tHeader = null
    if (ref && ref.current) {
        tHeader = ref.current.getElementsByClassName("ant-table-thead")[0]
    } else {
        tHeader = document.getElementsByClassName("ant-table-thead")[0]
    }
    //表格内容距离顶部的距离
    let tHeaderBottom = 0
    if (tHeader) {
        tHeaderBottom = tHeader.getBoundingClientRect().bottom
    }
    // 窗体高度-表格内容顶部的高度-表格内容底部的高度
    // let height = document.body.clientHeight - tHeaderBottom - extraHeight
    let height = `calc(100vh - ${tHeaderBottom + extraHeight}px)`
    // 空数据的时候表格高度保持不变,暂无数据提示文本图片居中
    if (ref && ref.current) {
        let placeholder = ref.current.getElementsByClassName('ant-table-placeholder')[0]
        if (placeholder) {
            placeholder.style.height = height
            placeholder.style.display = "flex"
            placeholder.style.alignItems = "center"
            placeholder.style.justifyContent = "center"
        }
    }
    return height
}

export function getParam(name: string): string | undefined {
    const reg = new RegExp(`(^|&)${name}=([^&]*)(&|$)`);
    const location: Location = window.location;
    const href = location.href;
    const query = href.substr(href.lastIndexOf('?') + 1);
    const res = query.match(reg);
    if (res !== null) {
        return decodeURIComponent(res[2])
    }
    return undefined;
}

export function parseParam2Obj(search: string) {
    if (search) {
        const tar = JSON.parse('{"' + search.replace(/"/g, '\\"').replace(/&/g, '","').replace(/=/g, '":"') + '"}')
        Object.keys(tar).forEach(key => {
            const value = tar[key]
            tar[key] = decodeURIComponent(value)
        })
        return tar
    }
    return {}
}

export function obj2UrlParam(obj: Record<any, any>) {
    return Object.entries(obj).map(([key, val]) => `${key}=${encodeURIComponent(val)}`).join('&')
}

export function saveJSON(data: any, filename: string) {

    if (!data) {
        console.error('No data')
        return;
    }

    if (!filename) filename = 'console.json'

    if (typeof data === "object") {
        data = JSON.stringify(data, undefined, 4)
    }

    var blob = new Blob([data], { type: 'text/json' }),
        e = document.createEvent('MouseEvents'),
        a = document.createElement('a')

    a.download = filename
    a.href = window.URL.createObjectURL(blob)
    a.dataset.downloadurl = ['text/json', a.download, a.href].join(':')
    e.initMouseEvent('click', true, false, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null)
    a.dispatchEvent(e)
}

export const data2Byte = (value: number) => {
	if (Object.prototype.toString.call(value) !== '[object Number]') return '-';

	const _UNIT = ['Byte', 'KB', 'MB', 'GB', 'TB', 'PB'];
	const _CARRY = 1024;
	let index = 0;
	let con = value;
	const isPositive = con >= 0 ? true : false;
	if (!isPositive) {
		con = con * -1;
	}
	while (con >= _CARRY && index < _UNIT.length - 1) {
		con = con / _CARRY;
		index++;
	}
	if (!isPositive) {
		con = con * -1;
	}
	return Number(con.toFixed(2)) + _UNIT[index];
};

export const data2Time = (value: number) => {
    if (Object.prototype.toString.call(value) !== '[object Number]') return '-';

    const _UNIT = ['秒', '分钟', '小时'];
    const _CARRY = 60;
    let index = 0;
    let con = value;
    const isPositive = con >= 0 ? true : false;
    if (!isPositive) {
        con = con * -1;
    }
    while (con >= _CARRY && index < _UNIT.length - 1) {
        con = con / _CARRY;
        index++;
    }
    if (!isPositive) {
        con = con * -1;
    }
    return Number(con.toFixed(2)) + _UNIT[index];
};

export const  isJsonString = (str:string) => {
  try {
    JSON.parse(str);
    return true;  // 如果解析成功，返回 true
  } catch (e) {
    return false;  // 如果解析失败，返回 false
  }
}

export const  isDomString = (str:string) => {
    const domRegex = /<\/?[a-z][\s\S]*>/i;
    return domRegex.test(str);
}
