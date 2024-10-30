import { App, CfnOutput, RemovalPolicy, Stack, StackProps } from 'aws-cdk-lib';
import { AuthorizationType, AwsIntegration, CognitoUserPoolsAuthorizer, ResponseType, RestApi } from 'aws-cdk-lib/aws-apigateway';
import { CloudFrontWebDistribution } from 'aws-cdk-lib/aws-cloudfront';
import { CfnUserPoolUser, CfnUserPoolUserToGroupAttachment, OAuthScope, UserPool, UserPoolClient } from 'aws-cdk-lib/aws-cognito';
import { Effect, PolicyDocument, PolicyStatement, Role, ServicePrincipal } from 'aws-cdk-lib/aws-iam';
import { BlockPublicAccess, Bucket } from 'aws-cdk-lib/aws-s3';
import { BucketDeployment, Source } from 'aws-cdk-lib/aws-s3-deployment';

export class WebsiteStack extends Stack {
  constructor(scope: App, id: string, props?: StackProps) {
    super(scope, id, props);

    // Create an S3 bucket for the website
    const websiteBucket = new Bucket(this, 'WebsiteBucket', {
      websiteIndexDocument: 'index.html',
      blockPublicAccess: BlockPublicAccess.BLOCK_ALL,
      removalPolicy: RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    // Create a CloudFront distribution to serve the website
    const distribution = new CloudFrontWebDistribution(this, 'WebsiteDistribution', {
      originConfigs: [
        {
          s3OriginSource: {
            s3BucketSource: websiteBucket,
          },
          behaviors: [{ isDefaultBehavior: true }],
        },
      ],
    });

    // Deploy the website files to S3
    new BucketDeployment(this, 'DeployWebsite', {
      sources: [Source.asset('../../frontend/out')],
      destinationBucket: websiteBucket,
      distribution,                 // Trigger invalidation after deploy
      distributionPaths: ['/*'],     // Invalidate all cache paths
    });

    const api = new RestApi(this, 'WebsiteApi', {
      restApiName: 'Website Service',
      description: 'This service serves the static website securely.',
    });
    
    // Create an integration with the S3 bucket
    const s3Integration = new AwsIntegration({
      service: 's3',
      integrationHttpMethod: 'GET',
      path: `${websiteBucket.bucketName}/{object}`,
      options: {
        credentialsRole: new Role(this, 'ApiGatewayS3Role', {
          assumedBy: new ServicePrincipal('apigateway.amazonaws.com'),
          inlinePolicies: {
            S3AccessPolicy: new PolicyDocument({
              statements: [
                new PolicyStatement({
                  actions: ['s3:GetObject'],
                  resources: [`${websiteBucket.bucketArn}/*`],
                  effect: Effect.ALLOW,
                }),
              ],
            }),
          },
        }),
        requestParameters: {
          'integration.request.path.object': 'method.request.path.object',
        },
        integrationResponses: [
          {
            statusCode: '200',
            selectionPattern: '.*',
            responseParameters: {
              'method.response.header.Content-Type': 'integration.response.header.Content-Type',
            },
          },
        ],
      },
    });
    
    const userPool = new UserPool(this, 'UserPool', {
      signInAliases: { username: true, email: true },
    });

    // const defaultUser = new CfnUserPoolUser(this, 'DefaultUser', {
    //   desiredDeliveryMediums: ['EMAIL'],
    //   forceAliasCreation: false,
    //   userPoolId: userPool.userPoolId,
    //   userAttributes: [{ name: 'email', value: 'petern@amazon.com' } ],
    //   username: "MA-Admin",
    // });

    // new CfnUserPoolUserToGroupAttachment(this, 'UserToGroupAttachment', {
    //   groupName: 'DefaultGroup',
    //   username: defaultUser.username!,
    //   userPoolId: userPool.userPoolId,
    // });

    const cognitoDomain = userPool.addDomain('UserPoolDomain', {
      cognitoDomain: {
        domainPrefix: 'migration-assistant',
      },
    });
    
    const userPoolClient = new UserPoolClient(this, 'UserPoolClient', {
      userPool,
      generateSecret: false,
      oAuth: {
        flows: {
          implicitCodeGrant: true, // Allows redirection after login
        },
        scopes: [OAuthScope.EMAIL, OAuthScope.OPENID],
        callbackUrls: [api.url],
      },
    });

    api.addGatewayResponse('Unauthorized', {
      type: ResponseType.UNAUTHORIZED,
      responseHeaders: {
        'WWW-Authenticate': `'Bearer realm="${api.restApiName}"'`,
      },
      statusCode: '401',
    });

    const authorizer = new CognitoUserPoolsAuthorizer(this, 'CognitoAuthorizer', {
      cognitoUserPools: [userPool],
    });
    
    // Add a root resource and method to handle file paths
    const rootResource = api.root.addResource('{object}');
    rootResource.addMethod('GET', s3Integration, {
      authorizationType: AuthorizationType.COGNITO,
      authorizer,
      requestParameters: { 'method.request.path.object': true },
      methodResponses: [{ statusCode: '200' }],
    });


    new CfnOutput(this, 'CognitoLoginUrl', {
      value: `https://${cognitoDomain.domainName}.auth.${this.region}.amazoncognito.com/login?client_id=${userPoolClient.userPoolClientId}&response_type=token&scope=email+openid&redirect_uri=${api.url}`,
      description: 'Cognito Hosted UI Login URL',
    });
  }
}
