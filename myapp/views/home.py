import copy
import json
import logging
import os.path
import random
import traceback

from flask_appbuilder.baseviews import expose_api
from flask_babel import gettext as __
from flask_babel import lazy_gettext as _
from flask import g
import pysnooper
import datetime
from flask import jsonify
from markupsafe import Markup

from myapp import conf
from myapp.views.base import BaseMyappView

from flask_appbuilder import expose
from myapp import appbuilder
from flask import stream_with_context, request

class Myapp(BaseMyappView):
    route_base = '/myapp'
    default_view = 'home'  # 设置进入蓝图的默认访问视图（没有设置网址的情况下）

    @expose_api(description="顶部右侧导航按钮",url='/navbar_right')
    def navbar_right(self):
        data = [
            {
                "icon": '<svg t="1680839424970" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="6272" width="200" height="200"><path d="M512.192 0.704C230.848 0.704 0.704 230.848 0.704 512.192s230.144 511.488 511.488 511.488c281.28 0 511.488-230.208 511.488-511.488C1023.68 230.848 793.472 0.704 512.192 0.704z m0 959.04c-249.344 0-447.552-198.208-447.552-447.552 0-249.344 198.208-447.552 447.552-447.552 249.408 0 447.552 198.208 447.552 447.552 0 249.344-198.144 447.552-447.552 447.552z" fill="" p-id="6273"></path><path d="M576.896 598.848h173.888V526.08H576.896v-51.776c0-24.064 2.24-41.792 6.72-53.184 1.728-4.544 2.624-8.896 2.624-12.992s-6.208-6.08-18.816-6.08h-79.232V716.8H401.6V545.728c0-23.552 2.24-41.088 6.72-52.352 2.304-5.44 3.392-10.112 3.392-14.016 0-3.84-5.824-5.76-17.6-5.76h-77.824v243.2h-100.16v75.008H802.88V716.8H576.896V598.848z m-14.208-382.784c2.624-2.752 6.528-5.696 11.52-8.896 5.056-3.136 7.424-6.784 7.424-10.88 0-3.2-1.728-5.696-5.376-7.488-3.648-1.856-36.608-10.688-98.88-26.624-47.36 123.584-145.728 211.456-295.04 263.744 17.6 14.528 38.72 37.44 63.552 68.8 123.648-61.376 213.632-132.416 270.08-213.312 58.688 87.232 146.176 157.888 262.656 211.968 23.36-36.8 44.48-65.856 63.488-87.232-61.376-14.976-116.224-39.168-164.992-72.512-48.896-33.472-86.976-72.64-114.432-117.568z" fill="" p-id="6274"></path></svg>',
                "link": "%s/frontend/ai_hub/model_market/model_visual" % request.host_url.strip('/')
            }
        ]
        if conf.get('DOCUMENTATION_URL',''):
            data.append(
                {
                    "text": __("文档"),
                    "icon": '<svg t="1663658395713" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="4531" width="64" height="64"><path d="M808.35715 213.332736c-164.707272-164.709319-432.683537-164.709319-597.333504 0-164.709319 164.649967-164.709319 432.624185 0 597.333504 164.649967 164.709319 432.626231 164.709319 597.333504 0C973.067492 645.956921 973.067492 377.982704 808.35715 213.332736zM765.48983 767.767198c-141.075039 141.077086-370.609783 141.077086-511.627517 0-141.078109-141.017734-141.078109-370.520755 0-511.596817 141.017734-141.017734 370.552477-141.077086 511.627517 0C906.506541 397.188114 906.506541 626.750487 765.48983 767.767198z" p-id="4532" fill="#3273f1"></path><path d="M500.686838 686.040848c-20.432355 0.061398-37.063127 16.692171-37.063127 37.095873 0 20.458961 16.630772 37.090756 37.092803 37.090756 20.432355 0 37.066197-16.631796 37.066197-37.151132C537.781688 702.672644 521.147846 686.040848 500.686838 686.040848z" p-id="4533" fill="#3273f1"></path><path d="M505.832022 265.144776c-72.362075 0-136.290059 41.640376-158.933779 103.683431-5.26491 14.508435-9.813506 38.620599-5.26491 58.753125 3.048429 13.81975 17.709337 22.974247 31.320333 19.863397 14.117532-3.171226 23.0029-17.23043 19.832697-31.290657-1.556449-7.210215-0.060375-20.132526 3.350304-29.435403 12.533454-34.342156 51.27378-69.043493 109.60735-69.043493 68.681242 0 116.635417 35.091216 116.635417 85.375459 0 37.572734-23.302729 51.1561-64.525596 72.034617-37.303604 18.847254-83.761706 42.241057-83.761706 101.289917L474.092134 629.981065c0 14.478759 11.784394 26.2652 26.204825 26.2652 14.449084 0 26.235524-11.786441 26.235524-26.2652l0-53.606919c0.060375-25.605168 18.936281-36.317137 55.042617-54.504358 41.6107-20.968567 93.421716-47.025013 93.421716-118.820176C674.997839 321.862545 605.418135 265.144776 505.832022 265.144776z" p-id="4534" fill="#3273f1"></path></svg>',
                    "link": conf.get('DOCUMENTATION_URL', '')
                }
            )
        if conf.get('BUG_REPORT_URL',''):
            data.append(
                {
                    "icon": '<svg t="1667208826607" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="2544" width="64" height="64"><path d="M946.704566 523.521404c-7.757684-4.228301-17.560958-6.198166-30.852682-6.198166l-101.187587 0L814.664298 364.109742l85.525885-85.525885c6.120394-6.120394 14.257725-15.764032 14.257725-28.798906s-8.136308-22.678512-14.256702-28.797883c-7.404644-7.405667-15.780405-14.257725-26.832112-14.257725-11.050684 0-19.425422 6.852058-26.831089 14.257725l-85.525885 85.526909L302.644855 306.513976 217.118969 220.986043c-7.513114-7.513114-15.136745-14.257725-25.753547-14.257725-10.617825 0-18.240433 6.743588-25.753547 14.257725-6.898107 6.897084-14.256702 15.189957-14.256702 26.333762s7.358595 19.436678 14.256702 26.334785l85.526909 85.526909 0 156.351977-101.187587 0c-45.176922 0-48.688909 30.187533-48.688909 39.439244 0 11.543917 4.744048 38.395472 48.688909 38.395472l101.515045 0c2.040473 48.502667 13.470803 100.372012 30.578436 138.500401l-98.322329 110.534466-0.205685 0.23536c-18.582217 21.766746-18.540262 45.980217 0.109494 63.190181l0.462534 0.409322c9.954723 8.469905 15.636119 9.355065 26.227338 9.355065l0.192382 0c12.818957 0 25.266453-6.14086 35.994796-17.758456l85.244476-96.387257c26.178219 21.829168 92.261287 68.590168 177.956018 68.590168l15.349593 0L525.053294 403.815045l15.443737 0 0 466.222397 15.349593 0c74.453712 0 143.739728-43.435255 170.071444-62.098313l93.437066 92.929506c8.67559 9.286504 21.198811 14.603603 34.426067 14.603603 1.143033 0 2.199085 0.031722 3.189645 0.059352 7.123234 0.203638 16.853853 0.474814 26.76969-10.162454 9.119705-9.222035 11.04352-18.653849 11.04352-24.965601 0-15.264659-10.741645-27.739784-18.777669-35.752272l-100.250238-100.769055c18.494213-37.081547 35.811624-93.978395 38.534642-151.111626l101.558024 0c13.285584 0 23.110347-2.003634 30.91715-6.307659 11.460006-6.315846 17.770735-17.500583 17.770735-31.491225C964.538747 540.959565 958.205505 529.789155 946.704566 523.521404zM931.949514 559.579645c-2.064009 1.136893-6.531763 2.493797-16.09763 2.493797L783.964088 562.073442l0 15.349593c0 61.841463-20.957311 127.190821-40.430828 161.738661l-5.705955 10.124592 116.461455 117.062136c9.324366 9.29776 9.797134 13.340843 9.797134 14.056134 0 1.12666-1.728364 2.937912-2.258437 3.465938l-0.471744 0.49221c-0.204661 0.223081-0.37453 0.394996-0.509606 0.524956-0.781806 0.023536-2.032286-0.014326-3.00852-0.040932-1.258667-0.035816-2.602268-0.071631-4.055362-0.071631-4.716418 0-9.230222-1.850138-12.072967-4.947685L728.436424 767.144004l-10.706853 8.632611c-0.73985 0.595564-70.215178 55.93187-146.531308 62.854537L571.198264 373.115859l-76.842109 0 0 465.633996c-43.455721-3.318582-80.450287-20.041452-104.807021-34.30941-29.958312-17.547655-48.057529-35.407418-48.221258-35.5691l-11.540847-11.545964L223.844138 877.122815c-4.596691 4.940522-9.450233 7.772011-13.33368 7.772011l-0.193405 0c-1.415232 0-2.984984 0-3.824095-0.053212-0.370437-0.251733-1.067308-0.76748-2.276856-1.786693-3.01159-2.793626-7.992021-7.953136 2.558265-20.37505l111.924115-125.82573-4.726651-9.327436c-14.823614-29.252231-32.133861-85.959767-32.133861-149.507082l0-15.349593L149.951197 562.67003c-9.783831 0-14.128789-1.660826-15.847943-2.651386-1.101077-0.633427-2.140757-1.232061-2.140757-5.045923 0-3.054569 0-8.740058 17.989723-8.740058l131.886773 0L281.838993 346.465896 187.320293 251.948219c-2.122337-2.122337-3.450589-3.612271-4.27742-4.627391 0.826831-1.01512 2.155083-2.505054 4.27742-4.626367 1.76111-1.76111 3.072989-2.990101 4.045129-3.845585 0.972141 0.855484 2.284019 2.084475 4.046153 3.845585l94.517677 94.5187 483.788471 0 94.517677-94.5187c2.478448-2.477424 4.108574-3.849678 5.123694-4.604878 1.01512 0.754177 2.64627 2.12643 5.123694 4.604878 4.91494 4.913916 5.26184 7.073092 5.265934 7.073092-0.002047 0.020466-0.335644 2.177596-5.265934 7.108908l-94.517677 94.517677 0 196.628286 131.886773 0c9.636474 0 14.107299 1.334391 16.162098 2.453888 1.020236 0.555655 1.826602 0.995677 1.826602 4.496407C933.839561 558.537919 933.005566 558.997384 931.949514 559.579645z" p-id="2545"></path><path d="M714.75789 253.198699c0-48.649-18.896372-94.337575-53.207829-128.649032-34.311457-34.31248-80.001055-53.208852-128.650055-53.208852-48.649 0-94.336552 18.896372-128.649032 53.208852-34.311457 34.311457-53.207829 80.000032-53.207829 128.649032l0 15.349593 363.714745 0L714.75789 253.198699zM382.51595 237.849106c7.713682-76.169797 72.214718-135.809105 150.384056-135.809105s142.671397 59.639309 150.385079 135.809105L382.51595 237.849106z" p-id="2546"></path></svg>',
                    "link": conf.get('BUG_REPORT_URL', '')
                }
            )

        # data = data if conf.get('BABEL_DEFAULT_LOCALE', 'zh') == 'zh' else []
        data = conf.get('NAVBAR_RIGHT',None) if conf.get('NAVBAR_RIGHT',None)!=None else data
        # 返回模板
        return jsonify(data)

    # 左侧平台导航栏：返回空数组时前端不渲染，非空时在最左侧显示平台切换栏（默认收起）
    @expose_api(description="左侧平台导航栏", url='/navbar_left')
    def navbar_left(self):
        data = conf.get('NAVBAR_LEFT', [])
        return jsonify(data)

    @expose_api(description="底部智能助手按钮",url='/navbar_bottom')
    def navbar_bottom(self):
        data=[]
        if conf.get('AI_ASSISTANT_URL', ''):
            data.append({
                "title":"AI智能客服",
                "icon": '<svg t="1778584163166" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="8247" width="200" height="200"><path d="M515.6 770.2c48.4 0 91.3-31.3 106.2-77.4 1-3.1-0.4-6.4-3.4-7.8-3-1.3-6.5-0.2-8.1 2.6-0.2 0.3-17.2 27.8-83.7 36.8-9.5 1.3-19.2 2-28.8 2-46.5 0-67.3-17.6-67.5-17.7-2.4-2.1-5.9-2.1-8.4-0.1-2.4 2-3 5.6-1.3 8.3 20.4 32.8 56.7 53.2 95 53.3z" fill="#662D91" p-id="8248"></path><path d="M808.3 398.9c-45.7-123.7-164-212.1-303.2-212.1-138.6 0-256.6 87.6-302.6 210.5-2.4-2.7-4.9-5.3-7.6-7.6C221 239.9 349.9 126 505.3 126c154.7 0 283.2 112.8 310.2 261.5-2.8 3.6-5.2 7.4-7.2 11.4z m64.6-40.5c-0.6 0-1.1 0.1-1.7 0.1C832.3 190 683.5 64.3 505.2 64.3 322 64.3 169.8 197 136.1 372.5c-33.5 6.2-57.9 35.5-57.7 69.6v139.5c0 39.1 31.4 70.8 70.1 70.8 21.8 0 41.1-10.3 53.9-26.1C233.4 708 296 774 376.2 809c1-2 2.2-3.9 3.5-5.7 1.3-1.6 2.7-3 3.9-3 1.2 0 2.4 0.4 3.4 1.1-18.5-13.8-85.2-84.4-99.7-183.1-6.3-43.4 26.2-86.1 64.1-93.1 60.8-11.3 121.3-24.2 182.1-35.3 38.7-7 65.1-28.3 81.2-63.6 3.8-8.3 9.3-25 11.8-49 0.6-3.6 3.7-6.3 7.4-6.3 2.4 0 4.6 1.2 6 3.1l1.7-1c24 34.8 71.5 111.9 78.3 193.1 7.8 92.9 3.5 156.5-67.6 221.6l-0.3 0.3c-1 1.1-1.6 2.5-1.6 4 0 1.9 1 3.7 2.6 4.7 0.6 0.2 1.2 0.6 1.8 0.8 0.5 0.1 0.9 0.2 1.4 0.3 0.5 0 0.9-0.1 1.3-0.3 1-0.5 2-1.1 3-1.7 72.6-40.1 127.2-106.4 152.5-185.4a72.29 72.29 0 0 0 45.2 30.2c-30 136.9-152.2 222.7-303.5 235.6-9.6-23.4-32.4-38.6-57.6-38.5-34.2 0-62 27.1-62 60.5s27.8 60.5 62 60.5c26.6 0.1 50.3-16.9 58.7-42.1 175.1-14.2 315.5-118.3 344.8-280 26.7-11 44.1-37 44.1-65.9V429.9c0.2-39.5-32-71.5-71.8-71.5z" fill="#662D91" p-id="8249"></path></svg>',
                "url": conf.get('AI_ASSISTANT_URL'),
            })
        return jsonify(data)
    @expose_api(description="顶部菜单侧边子菜单",url='/menu')
    # @pysnooper.snoop()
    def menu(self,is_admin=False):
        if g and hasattr(g,'user') and g.user and g.user.is_admin():
            is_admin=True
        # 项目空间
        projetc = {
            "name": 'group',
            "title": __('项目空间'),
            "isExpand": False,
            "isMenu": True,
            "icon": "lucide:folders",
            "children": [
                {
                    "name": 'project_group',
                    "title": __('项目组'),
                    "icon": "lucide:folder",
                    "isMenu": True,
                    "isExpand": True,
                    "children": [
                        {
                            "name": 'org_group',
                            "title": __('空间列表'),
                            "icon": "lucide:layout-list",
                            "menu_type": "api",
                            "url": "/project_modelview/space/api/",
                            "model_name": "project",
                            "related": [
                                {
                                    "hidden": 1,
                                    "name": 'project_user',
                                    "title": __('组成员'),
                                    "icon": "lucide:users",
                                    "menu_type": "api",
                                    "url": "/project_user_modelview/api/",
                                }
                            ]
                        },
                        {
                            "name": 'space_members',
                            "title": __('成员与配额'),
                            "icon": "lucide:user-cog",
                            "menu_type": "api",
                            "url": "/project_user_modelview/api/",
                        }
                    ]
                }
            ]
        }
        # 数据
        data = {
                "name": 'data',
                "title": __('数据资产'),
                'hidden': 0,
                "isMenu": True,
                "icon": "lucide:database",
                "children": [
                    {
                        "name": 'datasearch',
                        "title": __('数据探索'),
                        "icon": "lucide:search",
                        "isMenu": True,
                        "isExpand": True,
                        "children": [
                            {
                                "name": 'data_search',
                                "title": 'sqllab',
                                # "disable": True,
                                "icon": "lucide:file-search",
                                "menu_type": "innerRoute",
                                "url": "{host}/frontend/dataSearch".format(host=request.host_url.strip('/')) if request else '/frontend/dataSearch'
                            }
                        ]
                    },
                    {
                        "name": 'metadata',
                        "title": __('元数据'),
                        "icon": "lucide:book-open",
                        "isMenu": True,
                        "isExpand": True,
                        "children": [
                            {
                                "name": 'metadata_table',
                                "title": __('库表'),
                                "icon": "lucide:table",
                                "menu_type": "api",
                                "url": "/metadata_table_modelview/api/"
                            },
                            {
                                "name": 'metadata_metric',
                                "title": __('指标'),
                                "icon": "lucide:bar-chart",
                                "menu_type": "api",
                                "url": "/metadata_metric_modelview/api/"
                            },
                            {
                                "name": 'metadata_dimension',
                                "title": __('维表'),
                                # "disable":True,
                                "icon": "lucide:boxes",
                                "menu_type": "api",
                                "url": "/dimension_table_modelview/api/"
                            },
                        ]
                    },
                    {
                        "name": 'media_data',
                        "title": __('媒体数据'),
                        "icon": "lucide:film",
                        "isMenu": True,
                        "isExpand": True,
                        "children": [
                            {
                                "name": 'dataset',
                                "title": __('数据集'),
                                "icon": "lucide:library",
                                "menu_type": "api",
                                "url": "/dataset_modelview/api/"
                            },
                            {
                                "name": 'label_platform',
                                "title": __('标注平台'),
                                "icon": "lucide:tags",
                                "menu_type": "api",
                                "disable": True,
                                "url": "/metadata_table_modelview/api/"
                            }
                        ]
                    },

                ]
            }
        # 在线开发
        dev = {
                "name": 'dev',
                "title": __('在线开发'),
                'hidden': 0,
                "isExpand": True,
                "icon": "lucide:code",
                "children": [
                    {
                        "name": 'images',
                        "title": __('镜像管理'),
                        "icon": "lucide:package",
                        "isMenu": True,
                        "isExpand": True,
                        "children": [
                            {
                                "name": 'docker_repository',
                                "title": __('镜像仓库'),
                                "icon": "lucide:container",
                                "menu_type": "api",
                                "url": "/repository_modelview/api/"
                            },
                            {
                                "name": 'docker',
                                "title": __('镜像构建'),
                                "icon": "lucide:hammer",
                                "menu_type": "api",
                                "url": "/docker_modelview/api/"
                            },
                            {
                                "name": 'template_images',
                                "title": __('镜像管理'),
                                "icon": "lucide:boxes",
                                "menu_type": "api",
                                "url": "/images_modelview/api/"
                            },
                        ]
                    },
                    {
                        "name": 'dev_online',
                        "title": __('代码开发'),
                        "icon": "lucide:code",
                        "isMenu": True,
                        "isExpand": True,
                        "children": [
                            {
                                "name": 'notebook',
                                "title": 'notebook',
                                "icon": "lucide:file-edit",
                                "menu_type": "api",
                                "url": "/notebook_modelview/api/"
                            }
                        ]
                    },
                    {
                        "name": 'data_pipeline',
                        "title": __('数据开发'),
                        "icon": "lucide:workflow",
                        "isMenu": True,
                        "isExpand": True,
                        "children": [
                            {
                                "name": 'etl_pipeline',
                                "title": __('任务ETL'),
                                "icon": "lucide:workflow",
                                "menu_type": "api",
                                # "disable": True,
                                "url": "/etl_pipeline_modelview/api/",
                            },
                            {
                                "name": 'task_manager',
                                "title": __('任务管理'),
                                # "disable": True,
                                "icon": "lucide:list-checks",
                                "menu_type": "api",
                                "url": "/etl_task_modelview/api/",
                            },
                            {
                                "name": 'instance_manager',
                                "title": __('任务实例'),
                                "disable": True,
                                "icon": "lucide:play-circle",
                                "menu_type": "innerRoute",
                            }
                        ]
                    },
                ]
            }
        # 机器学习
        ml = {
                "name": 'train',
                "title": __('模型训练'),
                'hidden': 0,
                "isExpand": True,
                "icon": "lucide:cpu",
                "children": [
                    {
                        "name": 'train_template',
                        "title": __('模板开发'),
                        "icon": "lucide:layout-template",
                        "isMenu": True,
                        "isExpand": True,
                        "children": [
                            {
                                "name": 'job_template_group',
                                "title": __('模板分类'),
                                "icon": "lucide:folder-tree",
                                "menu_type": "api",
                                "url": "/project_modelview/job_template/api/",
                                "model_name": "project"
                            },
                            {
                                "name": 'job_template',
                                "title": __('任务模板'),
                                "icon": "lucide:file-code",
                                "menu_type": "api",
                                "url": "/job_template_fab_modelview/api/"
                            },
                        ]
                    },
                    {
                        "name": 'train_task',
                        "title": __('任务流'),
                        "icon": "lucide:git-branch",
                        "isMenu": True,
                        "isExpand": True,
                        "children": [
                            {
                                "name": 'pipeline',
                                "title": __('任务流'),
                                "icon": "lucide:git-branch",
                                "menu_type": "api",
                                "url": "/pipeline_modelview/api/",
                                "model_name": "pipeline",
                                "related": [
                                    {
                                        "hidden": 1,
                                        "name": 'task',
                                        "title": __('任务'),
                                        "icon": "lucide:list-todo",
                                        "menu_type": "api",
                                        "url": "/task_modelview/api/",
                                    }
                                ]
                            },
                            {
                                "name": 'runhistory',
                                "title": __('定时调度'),
                                "icon": "lucide:calendar-clock",
                                "menu_type": "api",
                                "url": "/runhistory_modelview/api/"
                            },
                            {
                                "name": 'workflow',
                                "title": __('运行实例'),
                                "icon": "lucide:history",
                                "menu_type": "api",
                                "url": "/workflow_modelview/api/"
                            },
                        ]
                    },
                    {
                        "name": 'automl',
                        "title": __('Automl'),
                        "icon": "lucide:sliders",
                        "isExpand": True,
                        "isMenu": True,
                        "children": [
                            {
                                "name": 'hyperparameter_search',
                                "title": __('超参搜索'),
                                "icon": "lucide:sliders",
                                "menu_type": "api",
                                "url": "/nni_modelview/api/"
                            }
                        ]
                    },
                ]
            }
        # 服务管理
        service = {
                "name": 'service',
                "title": __('服务管理'),
                "isMenu": True,
                # "isExpand": True,
                "icon": "lucide:server",
                "children": [
                    {
                        "name": 'total_resource',
                        "title": __('整体资源'),
                        "icon": "lucide:gauge",
                        "menu_type": "api",
                        "url": "/total_resource/api/",
                    },
                    {
                        "name": 'k8s_service',
                        "title": __('内部服务'),
                        "icon": "lucide:network",
                        "menu_type": "api",
                        "url": "/service_modelview/api/"
                    },
                    {
                        "name": 'inferenceservice',
                        "title": __('模型服务'),
                        "icon": "lucide:rocket",
                        "isMenu": True,
                        "isExpand": True,
                        "children": [
                            {
                                "name": 'model_manager',
                                "title": __('模型管理'),
                                "icon": "lucide:box",
                                "menu_type": "api",
                                "url": "/training_model_modelview/web/api/"
                            },
                            {
                                "name": 'inferenceservice_manager',
                                "title": __('推理服务'),
                                "icon": "lucide:rocket",
                                "menu_type": "api",
                                "url": "/inferenceservice_modelview/api/"
                            },
                            {
                                "name": 'llm_ingress',
                                "title": __('服务网关'),
                                "icon": "lucide:waypoints",
                                "menu_type": "api",
                                "disable": True,
                                "url": "/llm/api/"
                            },
                        ]
                    },
                    # {
                    #     "name": 'model_observability',
                    #     "title": '模型可观测',
                    #     "icon": "lucide:activity",
                    #     "menu_type": "api",
                    #     "disable": True,
                    #     "url": "/service_pipeline_modelview/api/"
                    # },
                ]
            }
        # 应用市场
        aihub = {
                "name": 'ai_hub',
                "title": 'AIHub',
                "isMenu": True,
                'hidden': 1,
                "isExpand": True,
                "icon": "lucide:store",
                "children": [
                    {
                        "name": 'model_market',
                        "title": __('模型市场'),
                        "icon": "lucide:store",
                        "isMenu": True,
                        'hidden': 0,
                        "isExpand": True,
                        "children": [
                            {
                                "name": 'model_visual',
                                "title": __('视觉'),
                                "icon": "lucide:image",
                                "menu_type": "api",
                                "url": "/model_market/visual/api/"
                            },
                            {
                                "name": 'model_voice',
                                "title": __('语音'),
                                "icon": "lucide:audio-lines",
                                "menu_type": "api",
                                "url": "/model_market/voice/api/"
                            },
                            {
                                "name": 'model_language',
                                "title": __('自然语言'),
                                "icon": "lucide:languages",
                                "menu_type": "api",
                                "url": "/model_market/language/api/"
                            },
                            {
                                "name": 'model_multimodal',
                                "title": __('多模态'),
                                "icon": "lucide:layers",
                                "menu_type": "api",
                                "url": "/model_market/multimodal/api/"
                            },
                            {
                                "name": 'model_aigc',
                                "title": __('大模型'),
                                "icon": "lucide:sparkles",
                                "menu_type": "api",
                                "url": "/model_market/aigc/api/"
                            },
                        ]
                    },
                    {
                        "name": 'other',
                        "title": __('智能体'),
                        "icon": "lucide:bot",
                        "isMenu": True,
                        "isExpand": True,
                        "children": [
                            {
                                "name": 'chat',
                                "title": __('智能对话'),
                                "icon": "lucide:message-square",
                                "menu_type": "api",
                                "url": '/chat_modelview/api/',
                                "disable": True
                            },
                            {
                                "name": 'chat-plugin',
                                "title": __('Agent配置'),
                                "icon": "lucide:bot",
                                "menu_type": "api",
                                "disable": True,
                                "url": '/chat_plugin_modelview/api/',
                            }
                        ]
                    },
                    {
                        "name": 'resource_rental',
                        "title": __('算力租赁'),
                        "icon": "lucide:server-cog",
                        "isMenu": True,
                        "isExpand": True,
                        "children": [
                            {
                                # innerRoute 根据 name 匹配前端 innerDynamicRouterConfigMap 的 key
                                "name": 'compute_leasing',
                                "icon": "lucide:server-cog",
                                "title": __('算力市场'),
                                "menu_type": "innerRoute",
                                "disable": True
                            },
                            {
                                "name": 'storage_lease',
                                "icon": "lucide:hard-drive",
                                "title": __('存储资源'),
                                "menu_type": "innerRoute",
                                "url": "/storageLease",
                                "disable": True
                            },
                            {
                                "name": 'resource_instance',
                                "title": __('实例管理'),
                                "icon": "lucide:monitor",
                                "menu_type": "api",
                                "disable": True
                            }
                        ]
                    },
                    {
                        "name": 'cost',
                        "title": __('费用'),
                        "icon": "lucide:wallet",
                        "isMenu": True,
                        "isExpand": True,
                        "children": [
                            {
                                "name": 'pod',
                                "title": __('计量计费'),
                                "icon": "lucide:receipt",
                                "menu_type": "api",
                                "url": "/pod_modelview/api/",
                                "disable": True
                            },
                            {
                                "name": 'bill',
                                "title": __('账单支付'),
                                "icon": "lucide:credit-card",
                                "menu_type": "api",
                                "url": "/bill_modelview/api/",
                                "disable": True
                            },
                            {
                                "name": 'recharge',
                                "title": __('充值'),
                                "icon": "lucide:wallet",
                                "menu_type": "innerRoute",
                                "url": "/recharge",
                                "disable": True
                            }
                        ]
                    },
                    {
                        "name": 'resource',
                        "title": __('资源配置(管理员)'),
                        "icon": "lucide:settings",
                        "isMenu": True,
                        "isExpand": True,
                        "children": [
                            {
                                "name": 'resource-node',
                                "title": __('机器资源'),
                                "icon": "lucide:cpu",
                                "menu_type": "api",
                                "url": "/node_modelview/api/" if is_admin else '',
                                "disable": True
                            },
                            {
                                "name": 'resource-store',
                                "title": __('存储资源'),
                                "icon": "lucide:hard-drive",
                                "menu_type": "api",
                                "url": "/storage_modelview/api/" if is_admin else '',
                                "disable": True
                            }
                        ]
                    }
                ]
            }
        # chat
        # 隐藏菜单
        chat= {
            "name": 'startchat',
            "title": __('数据智能'),
            "isMenu": True,
            'hidden': 1,
            "isExpand": True,
            'isMenuCollapsed': False,
            'isCollapsed': True,
            "icon": "lucide:messages-square",
            "children": [
                {
                    "name": 'chat',
                    "title": __('聊天'),
                    "icon": "lucide:message-square",
                    "menu_type": "iframe",
                    "isExpand": True,
                    'isMenuCollapsed': False,
                    'isCollapsed': True,
                    "url": '/frontend/distChat/',
                }
            ]
        }


        security_setting = {
            "name": 'security',
            "title": __('安全设置(管理员)'),
            "icon": "lucide:shield",
            "isMenu": True,
            "isExpand": True,
            "children": [
                {
                    "name": 'security-user',
                    "title": __('用户列表'),
                    "icon": "lucide:users",
                    "menu_type": "api",
                    "url": '/users/api/' if is_admin else "",
                    # "menu_type": "iframe",
                    # "url": '/users/list/?_flt_2_name=',
                    "disable":not is_admin
                },

				{
                    "name": 'security-logs',
                    "title": __('日志列表'),
                    "icon": "lucide:scroll-text",
                    "menu_type": "api",
                    "url": '/log_modelview/api/' if is_admin else "",
                    "disable": not is_admin
                },

            ]
        }

        # print(request.scheme)
        # print(request.scheme)
        # print(request.scheme)
        # print(request.scheme)
        # print(request.is_secure)

        links = {
            "name": 'link',
            "title": __('链接(管理员)'),
            'hidden': 0,
            "icon": "lucide:link",
            "isMenu": True,
            "isExpand": True,
            "children": [
                {
                    "name": link.get('name', ''),
                    "title": link.get('label', ''),
                    "icon": "lucide:link",
                    "menu_type": "out_link",
                    "disable": not is_admin,
                    "url": (link.get('url','') if 'http' not in link.get('url','') else link.get('url','')) if is_admin else "",
                } for link in conf.get('ALL_LINKS',[])
            ]
        }

        # print(request.host_url)
        if is_admin:
            projetc['children'].append(security_setting)

            # print(aihub['children'])
            projetc['children'].append(links)
        # if conf.get('BABEL_DEFAULT_LOCALE','zh')=='en':
        #     menu = [projetc, data, dev, ml, service]
        # else:
        menu = [projetc, data, dev, ml, service, aihub, chat]

        if conf.get('MENU', []):
            menu = conf.get('MENU', [])
        if conf.get('MENU_ADMIN', []) and is_admin:
            menu = conf.get('MENU_ADMIN', [])

        return menu

    @expose_api(description="每一页的弹窗接口",url='/feature/check')
    # @pysnooper.snoop()
    def featureCheck(self):
        url = request.values.get("url", type=str, default=None)
        # print(conf.get('alert_config',{}))
        for route in conf.get('alert_config', {}):
            # 用户自定义目录
            if url.replace("/frontend", '') == route.replace("/frontend", ''):
                try:
                    return jsonify(conf.get('alert_config', {})[route]())
                except Exception as e:
                    print(e)
                    data = {
                        'content': __('未能正常获取弹窗信息'),
                        'delay': 30000,
                        'hit': False,
                        'target': url,
                        'title': __('弹窗失败'),
                        'type': 'html',
                    }
                    # flash('未能正常获取弹窗信息', 'warning')
                    return jsonify(data)

        # flash('xxxxxxx','success')
        return jsonify({})

# add_view_no_menu添加视图，但是没有菜单栏显示
appbuilder.add_view_no_menu(Myapp)
