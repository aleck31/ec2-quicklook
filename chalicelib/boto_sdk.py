import ast


INSTANCE_TYPE_URL = 'https://aws.amazon.com/cn/ec2/instance-types/'


class EC2Client(object):
    def __init__(self, boto3_client):
        self._boto3_client = boto3_client

    #SDK: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html
    def get_instance_family(self):
        pass

    def get_instance_types(self, region, architecture, family):
        pass



class PricingClient(object):
    def __init__(self, boto3_client):
        self._boto3_client = boto3_client

    #SDK: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/pricing.html#Pricing.Client.describe_services
    def get_service_codes(self):
        '''Retrieve all AWS service codes'''
        try:
            svcodeList = []
            describe_args = {}
            while True:
                describe_result = self._boto3_client.describe_services(
                    **describe_args,
                    # FormatVersion='string',
                    # NextToken='string',
                    # MaxResults=100
                )
                svcodeList.extend(
                    [s['ServiceCode'] for s in describe_result['Services']]
                )
                if 'NextToken' not in describe_result:
                    break
                describe_args['NextToken'] = describe_result['NextToken']
            return {
                'count':len(svcodeList),
                'data':svcodeList
            }
        except Exception as ex:
            return str(ex)

        
    def get_service_attributes(self, service_code = 'AmazonEC2'):
        '''Retrieve all attribute names for one service'''
        try:
            describe_result = self._boto3_client.describe_services(
                ServiceCode = service_code,
            )['Services']
            attrList = describe_result[0].get('AttributeNames')
            return {
                'count':len(attrList),
                'data':attrList
            }
        except Exception as ex:
            return str(ex)


    def get_attribute_values(self, service_code = 'AmazonEC2', attribute_name = 'instanceType'):
        '''Retrieve available values for an attribute'''
        try:
            valueList = []
            describe_args = {
                    'ServiceCode' : service_code,
                    'AttributeName' : attribute_name,
            }
            while True:        
                response = self._boto3_client.get_attribute_values(
                    **describe_args
                )
                valueList.extend(
                    [a['Value'] for a in response['AttributeValues']]
                )
                if 'NextToken' not in response:
                    break
                describe_args['NextToken'] = response['NextToken']
            return {
                'count':len(valueList),
                'data':valueList
            }
        except Exception:
            pass


    def get_product_instance(self, region, instance_type, operation, 
        option='OnDemand',
        tenancy='Shared'):
        '''Get EC2 Instance Attributes and ListPrice [unit: Month]'''
        try:
            result = self._boto3_client.get_products(
                ServiceCode='AmazonEC2',
                Filters=[
                    {'Type': 'TERM_MATCH', 'Field': 'locationType','Value': 'AWS Region'},
                    {'Type': 'TERM_MATCH', 'Field': 'ServiceCode','Value': 'AmazonEC2'},
                    # {'Type': 'TERM_MATCH', 'Field': 'productFamily','Value': 'Compute Instance'},                    
                    {'Type': 'TERM_MATCH', 'Field': 'capacitystatus','Value': 'UnusedCapacityReservation'},         
                    {'Type': 'TERM_MATCH', 'Field': 'RegionCode','Value': region},
                    {'Type': 'TERM_MATCH', 'Field': 'instanceType','Value': instance_type},
                    {'Type': 'TERM_MATCH', 'Field': 'marketoption','Value': option},
                    {'Type': 'TERM_MATCH', 'Field': 'tenancy','Value': tenancy},                    
                    {'Type': 'TERM_MATCH', 'Field': 'operation','Value': operation},
                    # {'Type': 'TERM_MATCH', 'Field': 'operatingSystem','Value': os},
                    # {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw','Value': soft},
                ],
            )
            # 如果返回条目不唯一则说明给的参数值异常
            if len(result.get('PriceList')) != 1:
                raise ValueError('Unmatched parameters')
            
            # 通过 ast.literal_eval()函数 将字符串转为字典
            resultDict = ast.literal_eval(result['PriceList'][0])
            # 获取属性值并进行归类
            attrList = resultDict['product']['attributes']
            productMeta = {
                'instanceFamily': 'Compute optimized',
                'currentGeneration': 'Yes',
                'introduceUrl': INSTANCE_TYPE_URL + instance_type,
                'regionCode': 'us-east-1', 
                'location': 'US East (N. Virginia)',
                'tenancy': 'Shared',
                'capacitystatus': 'UnusedCapacityReservation',
                'usagetype': 'UnusedBox:c4.2xlarge',
                'instancesku': 'SVMA6TVRGD4B8MMP',
                'operation': 'RunInstances:0102', 
                'normalizationSizeFactor': '16',
                'ecu': '31',                
            }
            hardwareSpecs = {
                'physicalProcessor': 'Intel Xeon E5-2666 v3 (Haswell)',
                'clockSpeed': '2.9 GHz',
                'processorArchitecture': '64-bit',
                'vcpu': '8',
                'memory': '15 GiB',
                'dedicatedEbsThroughput': '1000 Mbps',
                'networkPerformance': 'High',
            }
            softwareSpecs = {
                'operatingSystem': 'Windows',
                'preInstalledSw': 'SQL Ent',
                'licenseModel': 'No License required',
            }            
            instanceSotrage = [
                {'volumeType': 'Instance Store',
                 'description': attrList['storage']}
            ]
            productFeature = {
                'intelTurboAvailable': 'Yes',
                'vpcnetworkingsupport': 'true',
                'enhancedNetworkingSupported': 'Yes',
                'classicnetworkingsupport': 'false',
                'intelAvx2Available': 'Yes',
                'intelAvxAvailable': 'Yes',
                'processorFeatures': 'Intel AVX; Intel AVX2; Intel Turbo',
            }        
            
            # 提取价格信息
            terms = next(iter(resultDict['terms'].get(option).values() ))
            priceDimensions = terms['priceDimensions']
            priceList = next(iter(priceDimensions.values()))
            # 提取单位价格和币种
            currency = next(iter(priceList['pricePerUnit']))
            value =  priceList['pricePerUnit'].get(currency)
            # 换算为月度费用并转换格式
            priceFormat = {
                'unit':'Month',
                'pricePerUnit': {
                    'currency': currency,
                    # 参考AWS做法按每月730h计算
                    'value': float(value)*730
                },
                'effectiveDate':terms['effectiveDate']
            }            
            priceList.update(priceFormat)

            prdInstance = {
                'productMeta':productMeta,
                'hardwareList': hardwareList,                
                'sotrageList':sotrageList,
                'softwareList':softwareList,
                'featureList':featureList,
                'listPrice':priceList,                
            }
            return prdInstance        
        
        except Exception as ex:
            return '%s: %s' %(self.__class__.__name__ ,ex)
        
        
        
    def get_product_volume(self, region, volume_type, volume_size:int, option='OnDemand'):
        '''Get EBS Volume Attributes and ListPrice [unit: GB-Mo]'''
        try:
            result = self._boto3_client.get_products(
                ServiceCode='AmazonEC2',
                Filters=[
                    {'Type': 'TERM_MATCH', 'Field': 'locationType','Value': 'AWS Region'},
                    {'Type': 'TERM_MATCH', 'Field': 'ServiceCode','Value': 'AmazonEC2'},
                    {'Type': 'TERM_MATCH', 'Field': 'productFamily','Value': 'Storage'},
                    {'Type': 'TERM_MATCH', 'Field': 'RegionCode','Value': region},
                    {'Type': 'TERM_MATCH', 'Field': 'volumeApiName','Value': volume_type}, 
                ],
            )
            # 如果返回条目不唯一则说明给的参数值异常
            if len(result.get('PriceList')) != 1:
                raise ValueError('Unmatched parameters')
            
            # 通过 ast.literal_eval()函数 将字符串转为字典
            resultDict = ast.literal_eval(result['PriceList'][0])
            # 获取属性值并进行归类
            attrList = resultDict['product']['attributes']
            
            productMeta = {
                'volumeType': 'General Purpose',
                'instanceFamily': 'Compute optimized',
                'storageMedia': 'SSD-backed',
                'usagetype': 'EBS:VolumeUsage.gp2',
            }
            productSpecs = {
                'maxThroughputvolume': '250 MiB/s',
                'maxIopsvolume': '16000',
                'maxVolumeSize': '16 TiB',
                'maxIopsBurstPerformance': '3000 for volumes <= 1 TiB',                
            }
#             volumeList = {
#                 'volumeType': volume_type,
#                 'volumeSzize': volume_size
#             }            
            # 提取价格信息
            terms = next(iter(resultDict['terms'].get(option).values() ))
            priceDimensions = terms['priceDimensions']
            priceList = next(iter(priceDimensions.values()))
            # 提取单位价格和币种
            currency = next(iter(priceList['pricePerUnit']))
            value =  priceList['pricePerUnit'].get(currency)
            # 换算为对应容量的月度费用并转换格式
            priceFormat = {
                'unit':'Month',
                'pricePerUnit': {
                    'currency': currency,
                    'value': float(value)*volume_size
                },
                'effectiveDate':terms['effectiveDate']
            }                        
            priceList.update(priceFormat)

            prdVolume = {
                'productMeta':productMeta,
                'productSpecs': productSpecs,                
#                 'volumeList':volumeList,
                'listPrice':priceList,                
            }
            return prdVolume 

        except Exception as ex:
            return '%s: %s' %(self.__class__.__name__ ,ex)
