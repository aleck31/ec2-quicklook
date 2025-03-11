new Vue({
  el: '#app',
  delimiters: ['[[', ']]'],  // Set delimiters for this instance
  mounted() {
    // Remove v-cloak after Vue is mounted
    this.$el.removeAttribute('v-cloak');
  },
  data: {
    form: {
      region: 'us-east-1',
      arch: 'x86_64',
      operation: '',
      family: '',
      type: '',
      voltype: 'gp3',
      volsize: 60
    },
    loading: false,
    validated: false,
    instance: null,
    volume: null,
    previousPrice: null,
    comparisonItems: [],
    regionOptions: [],
    operationOptions: [],
    familyOptions: [],
    typeOptions: [],
    voltypeOptions: [],
    detailUrl: null,
    familyState: null,
    familyFeedback: ''
  },
  computed: {
    isButtonDisabled() {
      return !this.form.type || this.loading || this.familyState === false;
    },
    priceChange() {
      if (!this.instance || !this.previousPrice) return null;
      const currentPrice = this.instance.listPrice.pricePerUnit.value;
      const change = ((currentPrice - this.previousPrice) / this.previousPrice) * 100;
      return change;
    },
    canCompare() {
      return this.instance && this.comparisonItems.length < 4;
    },
    hardwareItems() {
      return this.instance ? Object.entries(this.instance.hardwareSpecs).map(([key, value]) => ({
        key,
        value
      })) : [];
    },
    softwareItems() {
      return this.instance ? Object.entries(this.instance.softwareSpecs).map(([key, value]) => ({
        key,
        value
      })) : [];
    },
    featureItems() {
      return this.instance ? Object.entries(this.instance.productFeature).map(([key, value]) => ({
        key,
        value
      })) : [];
    },
    storageItems() {
      return this.instance ? Object.entries(this.instance.instanceStorage).map(([key, value]) => ({
        key,
        value
      })) : [];
    },
    volumeItems() {
      return this.volume ? Object.entries(this.volume.productSpecs).map(([key, value]) => ({
        key,
        value
      })) : [];
    },
    comparisonFields() {
      return [
        { key: 'type', label: 'Instance Type' },
        { key: 'price', label: 'Price' },
        { key: 'vcpu', label: 'vCPU' },
        { key: 'memory', label: 'Memory' },
        { key: 'network', label: 'Network Performance' }
      ];
    }
  },
  methods: {
    async quickLook() {
      this.loading = true;
      try {
        // Store previous price for comparison
        this.previousPrice = this.instance?.listPrice.pricePerUnit.value;

        // Query instance data
        const instanceResponse = await axios.get('product/instance', {
          params: {
            region: this.form.region,
            type: this.form.type,
            op: this.form.operation
          }
        });
        this.instance = instanceResponse.data;

        // Query volume data
        const volumeResponse = await axios.get('product/volume', {
          params: {
            region: this.form.region,
            type: this.form.voltype,
            size: this.form.volsize
          }
        });
        this.volume = volumeResponse.data;

        // Update detail URL
        this.detailUrl = `detail?region=${this.form.region}&type=${this.form.type}`;

      } catch (error) {
        console.error('Error fetching data:', error);
        this.$bvToast.toast('Failed to fetch data. Please try again.', {
          title: 'Error',
          variant: 'danger',
          solid: true
        });
      } finally {
        this.loading = false;
      }
    },
    async updateFamily() {
      // Reset validation state
      this.familyState = null;
      this.familyFeedback = '';
      
      try {
        const response = await axios.get('instance/family', {
          params: {
            region: this.form.region,
            arch: this.form.arch
          }
        });
        this.familyOptions = response.data.map(item => ({
          value: item.name,
          text: `${item.description}: ${item.name}`
        }));
        // Set default family if available
        if (this.familyOptions.length > 0) {
          const defaultFamily = this.familyOptions.find(f => ['m5', 'm6g'].includes(f.value));
          if (defaultFamily) {
            this.form.family = defaultFamily.value;
            this.updateTypes();
          }
        }
      } catch (error) {
        console.error('Error fetching families:', error);
        this.familyState = false;
        this.familyFeedback = 'Failed to load instance families. Please try again.';
      }
    },
    async updateTypes() {
      if (!this.form.family) return;
      
      try {
        // Store current size suffix before updating types
        const currentType = this.form.type;
        const currentSizeSuffix = currentType ? currentType.match(/[a-z]+\d*\.(.+)/)?.[1] : null;

        const response = await axios.get('instance/types', {
          params: {
            region: this.form.region,
            arch: this.form.arch,
            family: this.form.family
          }
        });

        if (response.data && response.data.length > 0) {
          this.typeOptions = response.data.map(item => ({
            value: item.instanceType,
            text: item.instanceType
          }));
          // Sort instance types by size
          this.typeOptions.sort((a, b) => {
            // Define size order mapping
            const sizeOrder = {
              'nano': 1, 'micro': 2, 'small': 3, 'medium': 4, 'large': 5,
              'xlarge': 6, '2xlarge': 7, '3xlarge': 8, '4xlarge': 9,
              '6xlarge': 10, '8xlarge': 11, '9xlarge': 12, '10xlarge': 13,
              '12xlarge': 14, '16xlarge': 15, '18xlarge': 16, '24xlarge': 17,
              '32xlarge': 18, '48xlarge': 19, 'metal': 20
            };
            
            // Extract size suffix (e.g., 'large', 'xlarge', '2xlarge')
            const getSizeSuffix = (type) => {
              const match = type.match(/[a-z]+\d*\.(.+)/);
              return match ? match[1] : '';
            };
            
            const sizeA = getSizeSuffix(a.value);
            const sizeB = getSizeSuffix(b.value);
            
            return (sizeOrder[sizeA] || 0) - (sizeOrder[sizeB] || 0);
          });

          // Set instance type with priority:
          // 1. Same size as current (e.g., if current is m5.4xlarge, try to find *.4xlarge)
          // 2. .large instance
          // 3. First available option
          let selectedType;
          if (currentSizeSuffix) {
            selectedType = this.typeOptions.find(t => t.value.endsWith(`.${currentSizeSuffix}`));
          }
          if (!selectedType) {
            selectedType = this.typeOptions.find(t => t.value.endsWith('.large')) || this.typeOptions[0];
          }
          this.form.type = selectedType.value;
          this.familyState = true;
          this.familyFeedback = '';
        } else {
          // Clear type options and show warning when no instance types are available
          this.typeOptions = [{
            value: '',
            text: 'No instance types available',
            disabled: true
          }];
          this.form.type = '';
          this.familyState = false;
          this.familyFeedback = `"${this.form.family}" is not supported in this region.`;
        }
      } catch (error) {
        console.error('Error fetching types:', error);
        this.typeOptions = [{
          value: '',
          text: 'Error loading instance types',
          disabled: true
        }];
        this.form.type = '';
        this.familyState = false;
        this.familyFeedback = 'Failed to load instance types. Please try again.';
      }
    },
    addToComparison() {
      if (!this.instance || this.comparisonItems.length >= 4) return;

      const item = {
        type: this.form.type,
        price: `${this.instance.listPrice.pricePerUnit.currency}${this.instance.listPrice.pricePerUnit.value.toFixed(2)}/${this.instance.listPrice.unit}`,
        vcpu: this.instance.hardwareSpecs.vCPU,
        memory: this.instance.hardwareSpecs.Memory,
        network: this.instance.hardwareSpecs['Network Performance']
      };

      this.comparisonItems.push(item);
      this.$bvModal.show('compare-modal');
    }
  },
  watch: {
    'form.arch'() {
      this.updateFamily();
    },
    'form.region'() {
      this.updateTypes();
    },
    'form.family'() {
      this.updateTypes();
    }
  },
  async created() {
    try {
      // Load initial data
      const [regionResponse, operationResponse, voltypeResponse] = await Promise.all([
        axios.get('instance/regions'),
        axios.get('instance/operations'),
        axios.get('instance/voltypes')
      ]);

      this.regionOptions = regionResponse.data.map(region => ({
        value: region.code,
        text: `${region.code} ${region.name}`
      }));

      this.operationOptions = operationResponse.data.map(op => ({
        value: op.operation,
        text: op.platform
      }));

      this.voltypeOptions = voltypeResponse.data.map(vt => ({
        value: vt,
        text: vt
      }));

      // Set default values
      this.form.operation = this.operationOptions.find(op => op.text === 'Linux/UNIX')?.value;
      await this.updateFamily();

    } catch (error) {
      console.error('Error loading initial data:', error);
    }
  }
});
