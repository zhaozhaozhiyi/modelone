import React from 'react'
import './LoadingStar.less';

export default function LoadingStar(props: { className?: string }) {
    return (
        <span className={`mo-loading ${props.className || ''}`} role="status" aria-label="加载中">
            <span className="mo-loading-ring" />
        </span>
    )
}
