import 'source-map-support/register';
import { App, DefaultStackSynthesizer } from 'aws-cdk-lib';
import { SolutionsInfrastructureStack, SolutionsInfrastructureStackProps } from '../lib/stack';

const getProps = () => {
//   const codeBucket = CODE_BUCKET;
//   const solutionVersion = CODE_VERSION;
//   const solutionId = 'SO0290';
//   const solutionName = SOLUTION_NAME;
//   const description = `(${solutionId}) - The AWS CloudFormation template for deployment of the ${solutionName}. Version ${solutionVersion}`;

  // Uncomment for local testing
  const codeBucket = 'unknown';
  const solutionVersion = "2.0.0";
  const solutionId = 'SO0290';
  const solutionName = 'migration-assistant-for-amazon-opensearch';
  const description = `(${solutionId}) - The AWS CloudFormation template for deployment of the ${solutionName}. Version ${solutionVersion}`;

  return {
    codeBucket,
    solutionVersion,
    solutionId,
    solutionName,
    description
  };
};

const app = new App();
const infraProps = getProps()
new SolutionsInfrastructureStack(app, 'OSMigrations-Bootstrap', {
  synthesizer: new DefaultStackSynthesizer({
    generateBootstrapVersionRule: false
  }),
    useExistingVpc: false,
  ...infraProps
});

new SolutionsInfrastructureStack(app, 'OSMigrations-Bootstrap-Existing-Vpc', {
    synthesizer: new DefaultStackSynthesizer({
      generateBootstrapVersionRule: false
    }),
    useExistingVpc: true,
    ...infraProps
  });