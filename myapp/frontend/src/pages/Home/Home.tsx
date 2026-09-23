import React from "react";
import { Typography } from "antd";
import {
  FileTextOutlined,
  DeploymentUnitOutlined,
} from "@ant-design/icons";
import FeatureCard from "./components/FeatureCard";
import PipelineList from "./components/PipelineList";
import "./Home.less";

const { Title } = Typography;

const Home: React.FC = () => {
  return (
    <div className="home-container">
      <div className="home-content">
        <section className="home-section">
          <div className="section-header">
            <Title level={5}>
              <DeploymentUnitOutlined /> {'平台主要功能'}
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
