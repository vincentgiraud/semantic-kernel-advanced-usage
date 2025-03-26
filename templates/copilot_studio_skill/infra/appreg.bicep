extension microsoftGraphV1

param clientAppName string
param today string = utcNow()

resource clientApp 'Microsoft.Graph/applications@v1.0' = {
  uniqueName: clientAppName
  displayName: clientAppName
  signInAudience: 'AzureADMyOrg'
  passwordCredentials: [
    {
      endDateTime: dateTimeAdd(today, 'P1Y')
    }
  ]
}

resource clientSp 'Microsoft.Graph/servicePrincipals@v1.0' = {
  appId: clientApp.appId
}

output clientAppId string = clientApp.appId
output clientSpId string = clientSp.id
// Not working
output clientSecret string = clientSp.passwordCredentials[0].secretText
