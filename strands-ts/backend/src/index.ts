import express, { Request, Response } from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';
import apiRoutes from './routes/api';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.resolve(__dirname, '../../.env') });

// AWS認証情報の確認
const checkAwsCredentials = (): void => {
  const awsAccessKeyId = process.env.AWS_ACCESS_KEY;
  const awsSecretAccessKey = process.env.AWS_SECRET_KEY;
  const awsRegion = process.env.AWS_DEFAULT_REGION;
  const awsSessionToken = process.env.AWS_SESSION_TOKEN;
  const awsBearerTokenBedrock = process.env.AWS_BEARER_TOKEN_BEDROCK;

  console.log('\n[AWS] Checking AWS credentials configuration...');

  const credentialsSet: string[] = [];
  const missingCredentials: string[] = [];

  if (awsAccessKeyId) {
    credentialsSet.push('AWS_ACCESS_KEY_ID');
  } else {
    missingCredentials.push('AWS_ACCESS_KEY_ID');
  }

  if (awsSecretAccessKey) {
    credentialsSet.push('AWS_SECRET_ACCESS_KEY');
  } else {
    missingCredentials.push('AWS_SECRET_ACCESS_KEY');
  }

  if (awsRegion) {
    credentialsSet.push(`AWS_REGION (${awsRegion})`);
  } else {
    console.log('[AWS] AWS_REGION not set, default will be used (us-east-1)');
  }

  if (awsSessionToken) {
    credentialsSet.push('AWS_SESSION_TOKEN (temporary credentials)');
  }

  if (awsBearerTokenBedrock) {
    credentialsSet.push('AWS_BEARER_TOKEN_BEDROCK (Bedrock API key)');
  }

  if (credentialsSet.length > 0) {
    console.log(`[AWS] ✓ Found ${credentialsSet.length} credential(s):`);
    credentialsSet.forEach(cred => console.log(`[AWS]   - ${cred}`));
  }

  if (missingCredentials.length > 0) {
    console.warn(`[AWS] ⚠ Missing required credentials: ${missingCredentials.join(', ')}`);
    console.warn('[AWS] ⚠ Bedrock API calls may fail without proper credentials.');
    console.warn('[AWS] ⚠ Please set the following environment variables:');
    missingCredentials.forEach(cred => console.warn(`[AWS]   - ${cred}`));
    console.warn('[AWS] ⚠ You can set them in .env file or use aws configure command.');
  } else {
    console.log('[AWS] ✓ All required AWS credentials are configured.');
  }

  // 複数の認証方法が設定されている場合
  if (awsAccessKeyId && awsSecretAccessKey && awsBearerTokenBedrock) {
    console.log('[AWS] ℹ Both access key credentials and Bedrock API key are set.');
    console.log('[AWS] ℹ Access key credentials will be used first.');
  }

  console.log('[AWS] AWS credentials check completed.\n');
};

checkAwsCredentials();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.use((req: Request, res: Response, next) => {
  const startTime = Date.now();
  const timestamp = new Date().toISOString();
  const clientIp = req.ip || req.socket.remoteAddress || 'unknown';
  
  console.log(`[${timestamp}] ${req.method} ${req.path} - IP: ${clientIp}`);
  
  res.on('finish', () => {
    const duration = Date.now() - startTime;
    const statusCode = res.statusCode;
    const statusColor = statusCode >= 500 ? '\x1b[31m' : statusCode >= 400 ? '\x1b[33m' : '\x1b[32m';
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.path} - ${statusColor}${statusCode}\x1b[0m - ${duration}ms`);
  });
  
  next();
});

app.get('/', (req: Request, res: Response) => {
  res.json({ message: 'Express + TypeScript Server' });
});

app.get('/api/health', (req: Request, res: Response) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.use('/api', apiRoutes);

app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});