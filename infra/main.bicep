param location string = 'westeurope'
param name string = 'rag-chatbot-app'
param servicePlanName string = '${name}-plan'
param appName string = '${name}-web'
param runtimeVersion string = 'PYTHON|3.10'

resource hostingPlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: servicePlanName
  location: location
  sku: {
    name: 'S1'
    tier: 'Standard'
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
  tags: {
    'azd-service-name': 'app-plan'
  }
}

resource webApp 'Microsoft.Web/sites@2022-03-01' = {
  name: appName
  location: location
  kind: 'app,linux'
  properties: {
    serverFarmId: hostingPlan.id
    siteConfig: {
      linuxFxVersion: runtimeVersion
    }
  }
  tags: {
    'azd-service-name': 'app'
  }
}

output appUrl string = webApp.properties.defaultHostName