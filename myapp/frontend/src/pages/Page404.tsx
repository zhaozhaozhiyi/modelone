import React from 'react'
import globalConfig from '../global.config'

export default function Page404() {
    return (
        <div className="d-f jc ac h100 fade-in">
            <div className="ta-c">
                <div><img className="w512" src={require('../images/workData.png')} alt=""/></div>
                <div>
                    <img className="pb32 w256" src={globalConfig.brand.logoUrl || globalConfig.appLogo.default} alt={globalConfig.brand.name} />
                </div>
                <div className="fs16">页面不存在</div>
            </div>
        </div>
    )
}
