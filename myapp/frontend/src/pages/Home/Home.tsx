import React from "react";
import { Typography } from "antd";
import {
  FileTextOutlined,
  DeploymentUnitOutlined,
} from "@ant-design/icons";
import FeatureCard from "./components/FeatureCard";
import PipelineList from "./components/PipelineList";
import globalConfig from "../../global.config";
import "./Home.less";

const { Title } = Typography;

const introSteps = ["准备数据", "编排训练", "注册模型", "发布服务"];

const Home: React.FC = () => {
  return (
    <div className="home-container">
      <div className="home-content">
        <section className="home-intro" aria-label={globalConfig.brand.name}>
          <div className="home-intro-brand">
            <img src={globalConfig.loadingLogo.default} width={36} height={36} alt="" />
            <div>
              <h2>{globalConfig.brand.name}</h2>
              <p>{`${globalConfig.brand.description.replace(/[。．.\s]+$/, "")}。数据、开发、训练、服务放在同一条流水线上。`}</p>
            </div>
          </div>
          <ol className="home-intro-steps">
            {introSteps.map((step, index) => (
              <li key={step}>
                <span className="home-intro-index">{index + 1}</span>
                <span className="home-intro-label">{step}</span>
              </li>
            ))}
          </ol>
        </section>
        <section className="home-section">
          <div className="section-header">
            <Title level={5}>
              <DeploymentUnitOutlined /> {'快速开始'}
            </Title>
          </div>
          <FeatureCard />
        </section>

        <section className="home-section">
          <div className="section-header">
            <Title level={5}>
              <FileTextOutlined /> {'流水线'}
            </Title>
          </div>
          <PipelineList />
        </section>
      </div>
    </div>
  );
};

export default Home;
