import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Theme } from '@twilio-paste/core/theme';
import { CustomizationProvider } from '@twilio-paste/core/customization';
import { Box } from '@twilio-paste/core/box';

// Components
import Layout from './components/Layout';
import ServicesPage from './pages/ServicesPage';
import ConversationsPage from './pages/ConversationsPage';
import ConversationDetailPage from './pages/ConversationDetailPage';
import ParticipantsPage from './pages/ParticipantsPage';
import MessagesPage from './pages/MessagesPage';
import WebhooksPage from './pages/WebhooksPage';
import MediaPage from './pages/MediaPage';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 2,
    },
  },
});

// Twilio Paste custom theme
const customTheme = {
  fonts: {
    fontFamilyText: 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif',
  },
  textColors: {
    colorTextBrandHighlight: '#0263E0',
  },
};

function App() {
  return (
    <CustomizationProvider baseTheme="default" theme={customTheme}>
      <Theme.Provider theme="default">
        <QueryClientProvider client={queryClient}>
          <Box minHeight="100vh" backgroundColor="colorBackgroundBody">
            <Router 
              future={{
                v7_startTransition: true,
                v7_relativeSplatPath: true
              }}
            >
              <Layout>
                <Routes>
                  <Route path="/" element={<Navigate to="/services" replace />} />
                  <Route path="/services" element={<ServicesPage />} />
                  <Route path="/conversations" element={<ConversationsPage />} />
                  <Route path="/conversations/:conversationSid" element={<ConversationDetailPage />} />
                  <Route path="/participants/:conversationSid" element={<ParticipantsPage />} />
                  <Route path="/messages/:conversationSid" element={<MessagesPage />} />
                  <Route path="/webhooks/:conversationSid" element={<WebhooksPage />} />
                  <Route path="/media/:conversationSid" element={<MediaPage />} />
                </Routes>
              </Layout>
            </Router>
          </Box>
        </QueryClientProvider>
      </Theme.Provider>
    </CustomizationProvider>
  );
}

export default App;
