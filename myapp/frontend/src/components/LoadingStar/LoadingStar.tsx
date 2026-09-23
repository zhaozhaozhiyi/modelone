import React from 'react'
import globalConfig from '../../global.config';
import './LoadingStar.less';

export default function LoadingStar(props: { className?: string }) {
    return (
        <span className={`mo-loading ${props.className || ''}`} role="status" aria-label="加载中">
            <span className="mo-loading-ring" />
            <img className="mo-loading-mark" src={globalConfig.loadingLogo.default} width={22} height={22} alt="" />
        </span>
    )
}
