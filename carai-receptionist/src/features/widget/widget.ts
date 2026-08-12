export interface WidgetConfig {
  primaryColor: string;
  brandName: string;
  greeting: string;
}

export const defaultWidgetConfig: WidgetConfig = {
  primaryColor: '#7c3aed',
  brandName: 'A Better Barber',
  greeting: 'Hi, how can I help today?',
};
