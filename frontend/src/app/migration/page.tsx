'use client';
import { useState } from 'react';
import Header from '@cloudscape-design/components/header';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Input from '@cloudscape-design/components/input';
import { Button } from '@cloudscape-design/components';

export default function Page() {
  const [value, setValue] = useState('');
  return (
    <SpaceBetween size="m">
      <Header variant="h1">Hello World!</Header>

      <SpaceBetween size="s">
        <span>Start editing to see some magic happen</span>
        <Input
          value={value}
          onChange={(event) => setValue(event.detail.value)}
        />
        <Button variant="primary">Click me</Button>
      </SpaceBetween>
    </SpaceBetween>
  );
}
