import React, { useEffect, useState } from 'react'
import { IAppMenuItem } from '../api/interface/kubeflowInterface'
import { getParam } from '../util'
import LoadingStar from '../components/LoadingStar/LoadingStar'
import './IframeTemplate.less'

export default function IframeTemplate(props?: IAppMenuItem) {
    const [url, setUrl] = useState(getParam('url') || props?.url)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        setUrl(getParam('url') || props?.url)
        setLoading(true)
    }, [props?.url])

    return (
        <div className="mo-iframe-page">
            {loading && (
                <div className="mo-iframe-loading">
                    <LoadingStar />
                </div>
            )}
            <iframe id="_frontendAppCustomFrame_"
                src={url}
                allowFullScreen
                allow="microphone;camera;midi;encrypted-media;"
                title={props?.title || '嵌入页面'}
                onLoad={() => setLoading(false)}
                className={`mo-iframe-frame ${loading ? 'mo-iframe-frame-loading' : ''}`}>
            </iframe>
        </div>
    )
}
