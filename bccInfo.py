#!/usr/bin/env python3
# coding=utf-8
# Author:ymc023
# Mail:
# Platform:
# Date:2022年01月25日 星期二 14时03分09秒

#导入Python标准日志模块
import logging
import datetime

import json
import datetime
import os
import sys 
from multiprocessing.pool import ThreadPool

try:
    import baidubce 
except Exception as e:
    print("baidubce sdk not installed. Ex:https://cloud.baidu.com/doc/Developer/index.html?sdk=python")
    sys.exit(1)


# 从Python SDK导入BCC配置管理模块以及安全认证模块
from baidubce.auth.bce_credentials import BceCredentials
from baidubce.bce_client_configuration import BceClientConfiguration
# 导入BCC相关模块
from baidubce.services.bcc import bcc_client
from baidubce.services.bcc import bcc_model
from baidubce.services.bcc import gpu_card_type
from baidubce.services.bcc import fpga_card_type
from baidubce.services.bcc.bcc_client import generate_client_token
from baidubce.services.bcc.bcc_model import EphemeralDisk




#设置日志文件的句柄和日志级别
logger = logging.getLogger('baidubce.http.bce_http_client')
fh = logging.FileHandler(
                        os.path.join(os.path.dirname(
                        os.path.realpath(__file__)),
                            "bccInfo.log"))
fh.setLevel(logging.DEBUG)

#设置日志文件输出的顺序、结构和内容
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.setLevel(logging.DEBUG)
logger.addHandler(fh)


def log(func):
    def inner(*args,**kwargs):
        res = func(*args,**kwargs)
        logger.info(f'func:{func.__name__}-{args}-{kwargs}:{res}')
        return res 
    return inner





class BccAll():
    def __init__(self, acc_id=None, acc_key=None,
                 bcm_host="bcc.su.baidubce.com"):
        self.bcm_host = bcm_host
        self.acc_id = acc_id
        self.acc_key = acc_key
        self.config = BceClientConfiguration(
            credentials=BceCredentials(
                self.acc_id, self.acc_key),
            endpoint=self.bcm_host,
            protocol = baidubce.protocol.HTTPS)
        self.client = bcc_client.BccClient(self.config)
        self.pool = ThreadPool(100)

    @log
    def getListInstances(self, internal_ip=None,
                         zone_name=None, max_keys=1000):
        '''
        max_keys: default 1000
        zone_name: cn-su-a、cn-su-b、cn-su-c,default all
        '''
        self.internal_ip = internal_ip
        self.zone_name = zone_name
        self.max_keys = max_keys
        # self.client.list_instances(marker="1")
        # 设置返回数据大小
        self.client.list_instances(max_keys=self.max_keys)
        # 通过internal Ip过滤虚机BCC列表
        self.client.list_instances(internal_ip=self.internal_ip)
        # 通过zone name过滤虚机BCC列表
        self.client.list_instances(zone_name=self.zone_name)
        # 执行查询虚机列表操作
        self.data = self.client.list_instances().instances
        return self.data

    @log
    def getInstanceRenewStatus(self, data) -> dict:
        self.mapRewnews = {}
        self.data = data
        try:
            for ins in self.data:
                self.mapRewnews.setdefault(ins.id,
                                           {}).update({"internal":ins.internal_ip})
                self.mapRewnews.setdefault(ins.id,
                                           {}).update({"name":ins.name.encode("utf-8").decode("utf-8")})
                self.mapRewnews.setdefault(ins.id,
                                           {}).update({"renew_status":ins.auto_renew})
                self.mapRewnews.setdefault(ins.id,
                                           {}).update({"public":ins.public_ip})

                # if ins.auto_renew != True:
                #    pass
                # else:
                #    self.mapData.setdefault(ins.id, []).append(ins.internal_ip)
                #    self.mapData.setdefault(ins.id, []).append(ins.name)
                #    self.mapData.setdefault(ins.id, []).append(ins.auto_renew)
            return self.mapRewnews
        except Exception as e:
            return {"error": f"{e}"}

    @log
    def getAllInstanceID(self, data) -> list:
        # 通过专属服务器DCC id过滤虚机BCC列表
        # self.client.list_instances(dedicated_host_id='your-choose-dedicated-host-id')
        self.data = data
        self.listData = []
        try:
            for ins in self.data:
                self.listData.append(ins.id)
            return self.listData
        except Exception as e:
            return {"error": f"{e}"}

    @log
    def getInstanceDetail(self, instance_id) -> baidubce.utils.Expando:
        self.ins_id = instance_id
        # 设置是否返回创建失败信息,True表示返回创建失败信息,默认为False
        self.contains_failed = True
        try:
            return (self.client.get_instance(self.ins_id,
                                             contains_failed=self.contains_failed).instance
                    )
        except Exception as e:
            return {"error": f"{e}"}

    @log
    def getInstanceInternalIP(self, instance_id):
        self.ins_id = instance_id
        self.mapIP = {}
        if isinstance(self.ins_id, str):
            try:
                self.ip = self.getInstanceDetail(self.ins_id).internal_ip
                return self.ip
            except Exception as e:
                return {f"{self.ins_id}": f"{e}"}

        if isinstance(self.ins_id, list):
            for idf in self.ins_id:
                try:
                    self.mapIP.setdefault(
                        (idf), []).append(
                        self.getInstanceDetail(idf).internal_ip)
                except Exception as e:
                    self.mapIP.setdefault(
                        (idf), []).append(f"{e}")
            return self.mapIP

    @log
    def getInstanceName(self, instance_id) -> str:
        self.ins_id = instance_id
        self.mapName = {}
        if isinstance(self.ins_id, str):
            try:
                return self.getInstanceDetail(self.ins_id).name
            except Exception as e:
                return {f"{self.ins_id}": f"{e}"}

        if isinstance(self.ins_id, list):
            for idf in self.ins_id:
                try:
                    self.mapName.setdefault(
                        (self.getInstanceInternalIP(idf)), []).append(
                        self.getInstanceDetail(idf).name)
                except Exception as e:
                    self.mapName.setdefault(
                        (idf), []).append(f"{e}")
            return self.mapName

    @log
    def getInstanceVNC(self, instance_id) -> dict:
        self.ins_id = instance_id
        self.mapVNC = {}
        if isinstance(self.ins_id, list):
            for idf in self.ins_id:
                try:
                    self.mapVNC.setdefault(
                        self.getInstanceInternalIP(idf), []).append(
                        self.client.get_instance_vnc(idf).vnc_url)
                except Exception as e:
                    self.mapVNC.setdefault(
                        self.getInstanceInternalIP(idf), []).append(f"{e}")
            return self.mapVNC

        if isinstance(self.ins_id, str):
            try:
                self.mapVNC.setdefault(self.getInstanceInternalIP(self.ins_id), []).append(
                    self.client.get_instance_vnc(self.ins_id).vnc_url)
                return self.mapVNC
            except Exception as e:
                return {f"{self.ins_id}": f"{e}"}

    @log
    def setInstanceCommand(self,
                           instance_id,
                           cmd=None,
                           imageid="m-fRxxx",
                           admin_pass="Q4a3QQAT6CM7EK1",
                           security_group_id="g-pc8",
                           force_stop=False
                           ):
        '''
        实现开机(start)，关机(stop,可带参数force_stop=True)，重启(restart),重装(rebuild),释放(release)
        当cmd=rebuild时，必须提供(
                               imageid,
                               admin_pass
                               有默认值
                               )
        newdata = client.setInstanceCommand(
                                            instance_id="i-fyEY",cmd="start/stop/restart/rebuild/release")
        '''
        self.ins_id = instance_id
        self.cmd = cmd
        self.image_id = imageid
        self.admin_pass = admin_pass
        self.security_group_id = security_group_id
        self.force_stop = force_stop
        if self.cmd == "start":
            try:
                return self.client.start_instance(self.ins_id)
            except Exception as e:
                return {"error": f"{self.ins_id}:{e}"}
        if self.cmd == "stop":
            try:
                # 设置关机是否计费，关机不计费为True，关机计费为False，默认为False。注意：只有白名单用户才可以实行关机不计费
                self.stop_with_no_charge = False
                return self.client.stop_instance(
                    instance_id=self.ins_id,
                    stopWithNoCharge=self.stop_with_no_charge,
                    force_stop=self.force_stop)
            except Exception as e:
                return {"error": f"{self.ins_id}:{e}"}
        if self.cmd == "restart":
            try:
                return self.client.reboot_instance(self.ins_id,
                                                   force_stop=self.force_stop)
            except Exception as e:
                return {"error": f"{self.ins_id}:{e}"}
        if self.cmd == "rebuild":
            try:
                return (self.client.rebuild_instance(self.ins_id,
                                                     self.image_id,
                                                     self.admin_pass))
            except Exception as e:
                return {"error": f"{self.ins_id}:{e}"}
        if self.cmd == "release":
            try:
                return self.client.release_instance(self.ins_id)
            except Exception as e:
                return {"error": f"{self.ins_id}:{e}"}
        if self.cmd == "newpassword":
            try:
                return self.client.modify_instance_password(self.ins_id,
                                                            self.admin_pass)
            except Exception as e:
                return {"error": f"{self.ins_id}:{e}"}
        if self.cmd == "bindsecgroup":
            try:
                return self.client.bind_instance_to_security_group(self.ins_id,
                                                                   self.security_group_id)
            except Exception as e:
                return {"error": f"{self.ins_id}:{e}"}
        if self.cmd == "unbindsecgroup":
            try:
                self.client.unbind_instance_from_security_group(self.ins_id,
                                                                self.security_group_id)
            except Exception as e:
                return {"error": f"{self.ins_id}:{e}"}

    @log
    def setInstanceResize(self, instance_id, destcpu=None, destmem=None):
        """
          Resizing the instance owned by the user.
          The Prepaid instance can not be downgrade.
          Only the Running/Stopped instance can be resized, otherwise, it's will get 409 errorCode.
          After resizing the instance,it will be reboot once.
          This is an asynchronous interface,
          you can get the latest status by BccClient.get_instance.

          :param instance_id:
              The id of instance.
          :type instance_id: string

          :param cpu_count:
              The parameter of specified the cpu core to resize the instance.
          :type cpu_count: int

          :param memory_capacity_in_gb:
              The parameter of specified the capacity of memory in GB to resize the instance.
          :type memory_capacity_in_gb: int

          :param client_token:
              An ASCII string whose length is less than 64.
              The request will be idempotent if client token is provided.
              If the clientToken is not specified by the user,
              a random String generated by default algorithm will be used.
              See more detail at
              https://bce.baidu.com/doc/BCC/API.html#.E5.B9.82.E7.AD.89.E6.80.A7
          :type client_token: string

          :return:
          :rtype baidubce.bce_response.BceResponse
        """
        self.ins_id = instance_id
        self.client_token = generate_client_token()
        self.destcpu = destcpu
        self.destmem = destmem
        try:
            if destcpu is not None and destmem is not None:
                return self.client.resize_instance(self.ins_id,
                                                   self.destcpu,
                                                   self.destmem,
                                                   self.client_token)
        except Exception as e:
            return {"reSize-error": f"{self.ins_id}:{e}"}

    @log
    def setInstanceRenew(self, instance_id):
        '''
        实例扩缩容期间不能进行续费操作。
        续费时若实例已欠费停机，续费成功后该实例将重新启动。
        支持关联的预付费CDS/EIP/MKT的产品一同续费，关联的后付费CDS/EIP/MKT不会一同续费
        '''
        # 设置你要操作的instance_id
        self.ins_id = instance_id
        #self.billing =  bcc_model.Billing('Postpaid')
        # 设为预付费
        self.billing = bcc_model.Billing('Prepaid', 1)
        self.client_token = generate_client_token()
        try:
            self.client.purchase_reserved_instance(self.ins_id,
                                                   self.billing,
                                                   self.client_token)
        except Exception as e:
            return {"renew-error": f"{self.ins_id}:{e}"}

    @log
    def createInstance(self,
                       imageid="x-fR7MF",
                       instance_type="N5",
                       admin_pass="Q4a3QQAT6CM7EK1",
                       #paid_billing = "Postpaid",
                       paid_billing="Prepaid",
                       cds_size_in_gb=100,
                       root_size_in_gb=80,
                       storage_type="enhanced_ssd_pl1",
                       instance_name="suz-newbcc",
                       zone_name="cn-su-a",
                       subnet_id="sbn-2t376",
                       security_group_id="g-upc8k3",
                       bcccpu=1,
                       bccmem=1,
                       auto_renew_time_unit="month",
                       auto_renew_time=0
                       ):
        # 如果用户未指定client_token参数,用uuid4生成一个随机字符串给client_token
        self.create_token = generate_client_token()
        # 输入你要创建instance使用的镜像ID
        self.imageid = imageid
        # 设置你要创建的实例类型
        self.instance_type = instance_type
        self.auto_renew_time_unit = auto_renew_time_unit
        self.auto_renew_time = auto_renew_time

        # 选择付费方式：
        # 付费方式为后付费
        #bcc_model.Billing('Postpaid', 1)
        # 付费方式为包年包月计费的预付费
        #bcc_model.Billing('Prepaid', 1)
        self.paid_billing = bcc_model.Billing(f"{paid_billing}", 1)

        # 创建cds_list所需参数：
        # 云磁盘大小(普通云磁盘范围：5~32765，高性能云磁盘范围：5~32765，SSD云磁盘范围：50~32765
        self.cds_size_in_gb = cds_size_in_gb

        self.root_size_in_gb = root_size_in_gb
        # 设置云磁盘类型
        # 具体类型对应见代码段下方的链接
        # https://cloud.baidu.com/doc/BCC/s/6jwvyo0q2#storagetype
        self.storage_type = storage_type

        # 根据CDS数据盘快照创建CDS盘数据时，输入用户选择的快照策略id
        #snap_shot_id = 'your-choose-snap-shot-id'

        # 实例名称
        self.instance_name = instance_name

        # 设置实例管理员密码(8-16位字符，英文，数字和符号必须同时存在，符号仅限!@#$%^*())
        self.admin_passwd = admin_pass

        # 指定zone信息，默 认为空，由系统自动选择，可通过调用查询可用区列表接口查询可用区列表
        # 格式为：国家-区域-可用区，如'中国-北京-可用区A'就是'cn-bj-a'
        self.zone_name = zone_name

        # 指定subnet信息，为空时将使用默认子网
        self.subnet_id = subnet_id
        # 指定security_group_id信息，为空时将使用默认安全组
        self.security_group_id = security_group_id

        # cpu memory
        self.bcccpu = bcccpu
        self.bccmem = bccmem

        # 输入你选择的gpu_card
        # 各gpu_card类型编码见下方『Gpu Type列表』
        # gpuCard='your-choose-Gpu-Type-id'

        # 输入你选择的fpga_card
        # 目前fpga_card类型只有KU115
        # fpgaCard='KU115'
        # 指定批量创建时的内网ip
        #internal_ips = ['192,168.113.110', '192,168.113.112']

        self.client.create_instance(cpu_count=self.bcccpu,
                                    memory_capacity_in_gb=self.bccmem,
                                    image_id=self.imageid,
                                    instance_type=self.instance_type,
                                    billing=self.paid_billing,
                                    root_disk_size_in_gb=self.root_size_in_gb,
                                    root_disk_storage_type=self.storage_type,
                                    #create_cds_list=bcc_model.CreateCdsModel,(cds_size_in_gb, storage_type, snap_shot_id)# 设置需要创建的CDS数据盘
                                    #create_cds_list=bcc_model.CreateCdsModel,(cds_size_in_gb,
                                                                              #storage_type),# 设置需要创建的CDS数据盘
                                    #network_capacity_in_mbps=1,# 设置创建BCC使用的网络带宽大小(必须在1~200之间)
                                    #purchase_count=1,# 批量创建BCC实例时使用，必须为大于0的整数
                                    # cardCount=1,#
                                    # 创建实例所要携带的GPU卡或FPGA卡数量，仅在gpuCard或fpgaCard字段不为空时有效
                                    name=self.instance_name,  # 设置创建BCC的名称
                                    admin_pass=self.admin_passwd,  # 设置实例管理员密码

                                    zone_name=self.zone_name,  # 设置创建BCC所在的zone
                                    subnet_id=self.subnet_id,  # 指定subnet信息，为空时将使用默认子网
                                    security_group_id=self.security_group_id,  # 指定securityGroup信息，为空时将使用默认安全组
                                    # gpuCard=gpuCard,#创建GPU实例时指定GPU类型
                                    # fpgaCard=fpgaCard,#创建FPGA实例时指定FPGA类型
                                    client_token=self.create_token)
                                    # internal_ips=internal_ips#指定批量创建时的内网IP)


if __name__ == '__main__':
    '''
    #初始化实例，传入access_id, access_key,
    bcm_host（即服务器所在区的地址,Ex:https://cloud.baidu.com/doc/BCC/s/0jwvyo603）
    client =BccAll(acc_id="TAKf8clU",acc_key="0095c4c5cbf1ad62",bcm_host="bcc.su.baidubce.com")

    #查询所有虚拟机列表
    data = client.getListInstances()

    #续费状态查询,return type dict
    newdata = client.getInstanceRenewStatus(data=data)
    print(json.dumps(newdata,indent=4))

    #查询所有id,return type list
    newdata = client.getAllInstanceID(data)
    print(newdata)

    #根据ID查询虚拟机详情
    newdata = client.getInstanceDetail(instance_id="i-fyuIL")
    print(newdata)

    #根据ID查内网IP,return type  str
    newdata = client.getInstanceInternalIP(instance_id="i-IULEY")
    print(newdata)

    #批量查询VNC地址,return type dict
    newdata = client.getInstanceInternalIP(instance_id=["i-bnr5","i-fEY"])
    newdata =client.getInstanceVNC(instance_id=client.getAllInstanceID(data))
    print(newdata)

    #resize 扩缩容
    newdata =client.setInstanceResize(instance_id="i-FdNY",destcpu=2,destmem=2)

    #实例开机(start)，关机(stop,可带参数force_stop=True)，重启(restart),重装(rebuild),释放(release)
    cmd=rebuild时，必须提供(
                               imageid,
                               admin_pass
                               有默认值
                               )
    newdata = client.setInstanceCommand(
                                            instance_id="i-fyEY",cmd="start/stop/restart/rebuild/release")

    newdata = client.setInstanceCommand(
                                            instance_id="i-FdN5",cmd="release")

       
    #paid_billing:Postpaid/Prepaid
        
    auto_renew_time=0/1自动续费１个月

    newdata = client.createInstance(
            paid_billing="Postpaid",
            root_size_in_gb=20,
            instance_name="test2",
            subnet_id="abn-sdey1svd",
            security_group_id="g-5fw284um",
            storage_type="enhanced_ssd_pl1",
            bcccpu=1,
            bccmem=1)

    '''

