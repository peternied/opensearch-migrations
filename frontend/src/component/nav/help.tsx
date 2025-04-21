import { HelpPanel } from '@cloudscape-design/components';
import DemoWrapper from '../demoWrapper';

export default function MAHelpPanel() {
  return (
    <HelpPanel header={<h2>Overview</h2>} key={'help'}>
      <DemoWrapper keyName="help-panel">
        Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus
        ex sapien vitae pellentesque sem placerat. In id cursus mi pretium
        tellus duis convallis. Tempus leo eu aenean sed diam urna tempor.
        Pulvinar vivamus fringilla lacus nec metus bibendum egestas. Iaculis
        massa nisl malesuada lacinia integer nunc posuere. Ut hendrerit semper
        vel class aptent taciti sociosqu. Ad litora torquent per conubia nostra
        inceptos himenaeos.
      </DemoWrapper>
    </HelpPanel>
  );
}
